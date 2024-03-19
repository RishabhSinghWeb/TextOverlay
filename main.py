from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
from textwrap import wrap
import getopt, sys, os

"""
    This script uses a image to apply gradually blur on it
    then it draw the given text to it
    
    usage:
        python3 main.py input_image.png output_image.png side "text"
            OR
        python3 main.py -i input_image.png -o output_image.png -s bottom -t "text"
"""

def center_crop(img, w_ratio, h_ratio):        
    w, h = img.size
    new_w = int(w/w_ratio) * w_ratio
    new_h = int(h/h_ratio) * h_ratio
    if new_w/new_h > w_ratio/h_ratio: # width more then ratio
        new_w = new_h * w_ratio/h_ratio
    elif new_h/new_w < w_ratio/h_ratio: # height more then ratio
        new_h = new_w * h_ratio/w_ratio
    left   = int(np.ceil(( w - new_w) / 2))
    right  = w - np.floor((w - new_w) / 2) # right = w - int(np.floor((w - new_w) / 2))
    top    = int(np.ceil(( h - new_h) / 2))
    bottom = h - int(np.floor((h - new_h) / 2))

    center_cropped_img = img.crop((left, top, right, bottom))
    return center_cropped_img

# def rounded_rectangle(draw, xy, rad, fill=None):
#     x0, y0, x1, y1 = xy
#     draw.rectangle([ (x0, y0 + rad), (x1, y1 - rad) ], fill=fill)
#     draw.rectangle([ (x0 + rad, y0), (x1 - rad, y1) ], fill=fill)
#     draw.pieslice([ (x0, y0), (x0 + rad * 2, y0 + rad * 2) ], 180, 270, fill=fill)
#     draw.pieslice([ (x1 - rad * 2, y1 - rad * 2), (x1, y1) ], 0, 90, fill=fill)
#     draw.pieslice([ (x0, y1 - rad * 2), (x0 + rad * 2, y1) ], 90, 180, fill=fill)
#     draw.pieslice([ (x1 - rad * 2, y0), (x1, y0 + rad * 2) ], 270, 360, fill=fill)

def display_text(display, image, text, h, w, font_path, font_size, margin = 10, autofit_text = True):
    image_text_ratio = 0.3      # amount of screen covered with text 0.6 for 60%
    text_shadow=15

    if(type(font_size) == str):
        if font_size[-1] == '%':
            font_size = int(int(font_size[:-1])*h/100)
        elif font_size[-2:] == 'px':
            font_size = int(font_size[:-2])
    font_margin = font_size//3
    font = ImageFont.truetype(font_path, font_size, encoding="unic")
    _,_, text_width, text_height = font.getbbox(text)
    font_height = font.getbbox("get Text overlay Height")[3] + font_margin    # 5+5 top and bottom margin
    while autofit_text:   # make the text fit in given image
        font_size -= 1
        font_margin = font_size//3
        font = ImageFont.truetype(font_path, font_size, encoding="unic")
        _,_, text_width, text_height = font.getbbox(text)
        font_height = font.getbbox("get Text overlay Height")[3] + font_margin    # 5+5 top and bottom margin
        if font_height*text_width/w/h < image_text_ratio or font_size < 8: autofit_text = False

    if margin == "auto":
        margin = min(margin, font_size)
    if side == 'left' or side == 'right':
        lines = min((h//font_height)-2, len(text.split()))
    elif side == 'top' or side == 'bottom':
        lines = text_width/(w*0.7) 
    else:
        input(f"Please set side to 'top', 'bottom', 'left' or 'right' only, while setting side to '{side}' doesn't work")
    if lines>1:
        lines = wrap(text, len(text)//lines + 4 , break_long_words=False) # word wrap
    else:
        lines = [text]

    for i in range(len(lines)):
        _,_, text_width, text_height = font.getbbox(lines[i])
        canvas = Image.new('RGBA', (text_width + font_margin*2, font_height),(0,0,0,text_shadow))
        canvas2 = Image.new('RGBA', ((text_width + font_margin*2)-int(font_size*0.7), font_height//2),(255,0,0,80))
        draw = ImageDraw.Draw(image)
        height_offset = i*font_height
        width_offset = w-text_width
        if side == 'left':
            x, y = margin, height_offset+font_height
        elif side == 'right':
            x, y = width_offset-10-margin, height_offset+font_height
        elif side == 'top':
            x, y = int(width_offset/2), height_offset+margin
        elif side == 'bottom':
            x, y = int(width_offset/2), h-(len(lines)-i)*font_height-margin

        if display == "shadow":
            blurred = canvas2.filter(ImageFilter.GaussianBlur(20))
            canvas2.paste(blurred, mask=canvas2)
            canvas.paste(canvas2, (font_size//2-2, font_size//2-2), canvas2)
            image.paste(canvas, (x, y), canvas)
        elif display == "text":
            draw.text((x+font_margin,y+font_margin//2), lines[i], fill=font_color, font=font)

    return image

def gradularBlur(image, side, w, h, blur_accuracy, blur_scale):
    length, reverse = h, 0
    if side == 'left' or side == 'right': length = w
    if side == 'left' or side == 'top': reverse = 1
    blur_accuracy = int(blur_accuracy)
    accuracy = length//blur_accuracy # blur pixels per cycle
    for i in range(blur_accuracy+1):
        fill = int(255* abs(reverse-(i/blur_accuracy))) 
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)
        if side == 'left' or side == 'right':
            draw.rectangle([ (accuracy*i, 0), accuracy*(i+1)-1, h ], fill=fill)
        elif side == 'top' or side == 'bottom':
            draw.rectangle([ (0, accuracy*i), w, accuracy*(i+1)-1 ], fill=fill)
        blurred = image.filter(ImageFilter.GaussianBlur(blur_scale))
        image.paste(blurred, mask=mask)

    return image

def generate(image_path, side='bottom', text=None, font_size='7%', font_path='Fonts/OpenSans.ttf', blur_accuracy=20,
             blur_scale=20, margin = 10, autofit_text = True):
    with Image.open(image_path) as image:
        image = center_crop(image, crop_ratio[0], crop_ratio[1])

        w,h = image.size
        if text:
            image = display_text(display="shadow",image=image, text=text, h=h, w=w, font_path=font_path, font_size=font_size, autofit_text=autofit_text)
        image = gradularBlur(image=image, side=side, w=w, h=h, blur_accuracy=blur_accuracy, blur_scale=blur_scale)
        if text:
            image = display_text(display="text",image=image, text=text, h=h, w=w, font_path=font_path, font_size=font_size, autofit_text=autofit_text)

        return image


if __name__ == '__main__':
    path = os.getcwd() + '/'
    # either use command line or these parameter
    side = 'bottom'
    image_path = path + 'input_image.png'
    output_path = path + 'output_image.png'
    font_path = path + 'Fonts/OpenSans.ttf'           # font location
    font_color = "white"                       # "white" for white text color or (255,255,255,255) for white text
    font_size = "6%"                           # 10% for height percent or 10px for size in pixels or a number
    autofit_text = True
    crop_ratio = (16,9)
    blur_accuracy = 20
    blur_scale = 20
    margin = "auto"                            # 10 for 10 pixel margin for text, "auto" for auto margin
    text = 'This is text overlay, it can automatically split into multiple lines if the text/font is too large and very large text will automatically fit inside the image'

    argumentList = sys.argv[1:]
    options = "h:i:o:s:t:f:"
    long_options = ["Help", "Input", "Output", "Side", "Text", "Font"]
    arguments, values = getopt.getopt(argumentList, options, long_options)
    for currentArgument, currentValue in arguments:
        if currentArgument in ("-h", "--Help"):
            print ("""usage:
                python3 main.py input_image.png output_image.png side "text"
            OR
                python3 main.py -i input_image.png -o output_image.png -s bottom -t "text"
                """)
        elif currentArgument in ("-i", "--Input"):  image_path = currentValue
        elif currentArgument in ("-o", "--Output"): output_path = currentValue
        elif currentArgument in ("-s", "--Side"):   side = currentValue.lower()
        elif currentArgument in ("-t", "--Text"):   text = currentValue
        elif currentArgument in ("-f", "--Font"):   font_path= currentValue
    if len(sys.argv)<7:
        try:
            image_path = sys.argv[1]
            output_path = sys.argv[2]
            side = sys.argv[3]
            text = sys.argv[4]
        except:
            pass

    image = generate(image_path = image_path, side = side, text = text, font_size=font_size, font_path=font_path,
                         margin = margin, autofit_text = autofit_text)

    # image.show()
    image.save(output_path)