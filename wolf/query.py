from paraCH import paraCH
import asyncio
import discord
import aiohttp
from urllib import parse
import json
from io import BytesIO
from PIL import Image, ImageChops, ImageDraw, ImageFont

cmds = paraCH()

TEST_APPID = "47PUQG-WKJJPXQK7G"

ENDPOINT = "http://api.wolframalpha.com/v2/query?"
WEB = "https://www.wolframalpha.com/"

# FONT = ImageFont.truetype("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf", 15, encoding="unic")
FONT = ImageFont.truetype("wolf/wolf_font", 15, encoding="unic")

# get the line size



def build_web_url(query):
    return "{}input/?i={}".format(WEB, parse.quoteplus(query))

async def get_query(query, appid, **kwargs):
    payload = {"input": query,
               "appid": appid,
               "format": "image,plaintext",
               "units": "metric",
               "output": "json"}
    payload.update(kwargs)

    async with aiohttp.get(ENDPOINT, params=payload) as r:
        if r.status == 200:
            data = await r.read()
            return json.loads(data)
        else:
            return None

async def send_file_embed(ctx, dest, filename, bytes_data, embed):
    data = await ctx.bot.http.send_file(dest.id, bytes_data, guild_id=dest.server.id,
                                       filename=filename, embed=embed.to_dict())
    return ctx.bot.connection._create_message(channel=dest, **data)

async def assemble_pod_image(atoms, dimensions):
    im = Image.new('RGB', dimensions, color=(255, 255, 255))
    draw = ImageDraw.Draw(im)
    for atom in atoms:
        if "text" in atom:
            draw.text(atom["coord"], atom["text"], fill=(0,0,0), font=FONT)
        if "image" in atom:
            im.paste(atom["image"], atom["coord"])
    return im

async def glue_pods(flat_pods):
    """
    Takes flat pods of the form (title, img, level).
    Return a Bytes object containing the glud together pods.
    """
    indent_width = 20
    before_title_gap = 10
    image_border = 5
    margin = 5

    split_height = 300

    splits = []
    atoms = []
    y_coord = 5
    max_width = 0

    for pod in flat_pods:
        if y_coord > split_height:
            splits.append( (atoms, (max_width, y_coord)) )
            max_width = 0
            y_coord = 5
            atoms = []

        indent = pod[2]*indent_width
        if pod[0]:
            atoms.append({"coord": (margin + indent, y_coord), "text": pod[0]})
            text_width, text_height = FONT.getsize(pod[0])
            y_coord += text_height
            max_width = max(text_width + indent + 2*margin, max_width)
        if pod[1]:
            y_coord += image_border
            atoms.append({"coord": (margin + indent + indent_width, y_coord), "image": pod[1]})
            y_coord += pod[1].height
            y_coord += image_border
            max_width = max(pod[1].width + indent + indent_width + image_border + margin, max_width)
    splits.append( (atoms, (max_width, y_coord)) )
    split_images = []
    for split in splits:
        split_images.append(await assemble_pod_image(*split))
    return split_images

async def flatten_pods(pod_data, level=0):
    """
    Takes the list of pods formatted as in wolf ouptut.
    Returns a list of flattened pods as accepted by glue_pods.
    """
    flat_pods = []
    for pod in pod_data:
        if "img" in pod:
            flat_pods.append((pod["title"], await handle_image(pod["img"]), level))
        elif "title" in pod:
            flat_pods.append((pod["title"], None, level))
        if "subpods" in pod:
            flat_pods.extend(await flatten_pods(pod["subpods"], level=level+1))
    return flat_pods


async def handle_image(image_data):
    """
    Takes an image dict as given by the wolf.
    Retrieves, trims (?) and returns an Image object.
    """
    target = image_data["src"]
    async with aiohttp.ClientSession() as session:
        async with session.get(target, allow_redirects=False) as resp:
            response = await resp.read()
    image = Image.open(BytesIO(response))
    return image
    # return smart_trim(image, border=10)

def smart_trim(im, border=0):
    bg = Image.new(im.mode, im.size, border)
    diff = ImageChops.difference(im, bg)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)


async def pods_to_image(pods):
    pass


async def handle_request(ctx, query, appid, simple=True, **kwargs):
    result = await get_query(query, appid, **kwargs)
    if result is None:
        await ctx.reply("I cannot communicate to Wolfram at the moment! Please try again in a moment.")
        return None
    resp = result["queryresult"]
    if not res["success"]:
        # TODO: Offer alternatives
        await ctx.reply("Wolfram Alpha didn't send back a result. Perhaps try rephrasing your query?")
        return None


@cmds.cmd("query",
          category="Maths",
          short_help="Sends a query to Wolfram Alpha",
          aliases=["wolf", "?", "??"])
async def cmd_query(ctx):
    """
    Usage:
        {prefix}? [query]
        {prefix}?? [query]
    Description:
        Sends the query to Wolf and returns the result.
        If used as ?, returns a short result.
        If used as ??, returns the full result.
    """
    result = await get_query(ctx.arg_str, TEST_APPID)
    print(result)
    result = await flatten_pods(result["queryresult"]["pods"])
    print(result)
    results = await glue_pods(result)

    for result in results:
        with BytesIO() as output:
            result.save(output, format="PNG")
            output.seek(0)
            await ctx.reply(file_data=output, file_name="wolf.png")
