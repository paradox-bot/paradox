from paraCH import paraCH
import discord
import asyncio
import aiohttp
from urllib import parse
import json
from io import BytesIO
from PIL import Image, ImageChops, ImageDraw, ImageFont

cmds = paraCH()
# Provides Wolf

ENDPOINT = "http://api.wolframalpha.com/v2/query?"
WEB = "https://www.wolframalpha.com/"

# truetype/liberation2/LiberationSans-Bold.ttf
FONT = ImageFont.truetype("resources/wolf_font.ttf", 15, encoding="unic")


def build_web_url(query):
    """
    Returns the url for Wolfram Alpha search for this query.
    """
    return "{}input/?i={}".format(WEB, parse.quote_plus(query))


async def get_query(query, appid, **kwargs):
    """
    Fetches the provided query from the Wolfram Alpha computation engine.
    Has a set of default arguments for the query.
    Any keyword arguments will over-write the defaults.
    Returns the response as a dictionary, or None if the query failed.
    Arguments:
        query: The query to post.
        appid: The Wolfram Appid to use in the query.
        kwargs: Params for the query.
    Returns:
        Dictionary containing results or None if an http error occured.
    """
    # Default params
    payload = {"input": query,
               "appid": appid,
               "format": "image,plaintext",
               "units": "metric",
               "output": "json"}

    # Allow kwargs to overwrite and add to the default params
    payload.update(kwargs)

    # Get the query response
    async with aiohttp.get(ENDPOINT, params=payload) as r:
        if r.status == 200:
            # Read the response, interp as json, and return
            data = await r.read()
            return json.loads(data.decode('utf8'))
        else:
            # If some error occurs, unintelligently fail out
            return None


async def assemble_pod_image(atoms, dimensions):
    """
    Draws the given atoms onto a canvas of the given dimensions.
    Arguments:
        atoms: A list of dictionaries containing:
            coords, the coordinates to draw the atom.
            text, text to draw at these coords.
            image, the image to paste at these coords.
        dimensions: A tuple (x,y) representing the size of the canvas to draw on.
    Returns:
        An image of the given dimensions with the given atoms drawn on.
    """
    # Make the canvas
    im = Image.new('RGB', dimensions, color=(255, 255, 255))
    draw = ImageDraw.Draw(im)

    # Iterate through the atoms and paste or write each one on as appropriate
    for atom in atoms:
        if "text" in atom:
            draw.text(atom["coord"], atom["text"], fill=(0, 0, 0), font=FONT)
        if "image" in atom:
            im.paste(atom["image"], atom["coord"])
    return im


async def glue_pods(flat_pods):
    """
    Turns a complete list of flattened pods into a list of images, split appropriately.
    Arguments:
        flat_pods: A list of tuples of the form (title, img, level)
    Returns:
        A list of PIL images containing the given pods glued and split as required.
    """
    indent_width = 10
    image_border = 5
    margin = 5

    split_height = 300

    splits = []
    atoms = []
    y_coord = 5
    max_width = 0

    for pod in flat_pods:
        if y_coord > split_height:
            splits.append((atoms, (max_width, y_coord)))
            max_width = 0
            y_coord = 5
            atoms = []

        indent = pod[2] * indent_width
        if pod[0]:
            atoms.append({"coord": (margin + indent, y_coord), "text": pod[0]})
            text_width, text_height = FONT.getsize(pod[0])
            y_coord += text_height
            max_width = max(text_width + indent + 2 * margin, max_width)
        if pod[1]:
            y_coord += image_border
            atoms.append({"coord": (margin + indent + indent_width, y_coord), "image": pod[1]})
            y_coord += pod[1].height
            y_coord += image_border
            max_width = max(pod[1].width + indent + indent_width + image_border + margin, max_width)
    splits.append((atoms, (max_width, y_coord)))
    split_images = []
    for split in splits:
        split_images.append(await assemble_pod_image(*split))
    return split_images


async def flatten_pods(pod_data, level=0, text=False, text_field="plaintext"):
    """
    Takes the list of pods formatted as in wolf ouptut.
    Returns a list of flattened pods as accepted by glue_pods.
    """
    flat_pods = []
    for pod in pod_data:
        if "img" in pod and not text:
            flat_pods.append((pod["title"], await handle_image(pod["img"]), level))
        elif text_field in pod and text:
            flat_pods.append((pod["title"], pod[text_field], level))
        elif "title" in pod:
            flat_pods.append((pod["title"], None, level))
        if "subpods" in pod:
            flat_pods.extend(await flatten_pods(pod["subpods"], level=level + 1, text=text))
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
    return smart_trim(image, border=10)


def smart_trim(im, border=0):
    bg = Image.new(im.mode, im.size, border)
    diff = ImageChops.difference(im, bg)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)


async def pods_to_filedata(pod_data):
    flat_pods = await flatten_pods(pod_data)
    images = await glue_pods(flat_pods)
    output_data = []
    for result in images:
        output = BytesIO()
        result.save(output, format="PNG")
        output.seek(0)
        output_data.append(output)
    return output_data


async def pods_to_textdata(pod_data):
    flat_pods = await flatten_pods(pod_data, text=True)
    tabchar = "​ "
    tab = tabchar * 2

    fields = []
    current_name = ""
    current_lines = []
    for title, text, level in flat_pods:
        if level == 0:
            if current_lines:
                fields.append((current_name if current_name else "Pod", "\n".join(current_lines), 0))
            current_name = title
            current_lines = []
        elif title:
            current_lines.append("{}**{}**".format(tab * level, title))
        if text:
            current_lines.append("{}{}".format(tab * (level + 1), text))
    return fields


def triage_pods(pod_list):
    if "primary" in pod_list[0] and pod_list[0]["primary"]:
        return (pod_list[0], pod_list[1:])
    else:
        important = [pod_list[0]]
        important.extend([pod for pod in pod_list if ("primary" in pod and pod["primary"])])
        if len(important) == 1 and len(pod_list) > 1:
            important.append(pod_list[1])
        extra = [pod for pod in pod_list[1:] if pod not in important]
        return (important, extra)


@cmds.cmd("query",
          category="Maths",
          short_help="Sends a query to Wolfram Alpha",
          aliases=["ask", "wolf", "w", "?w"])
@cmds.execute("flags", flags=["text"])
async def cmd_query(ctx):
    """
    Usage:
        {prefix}w [query] [--text]
    Description:
        Sends the query to the Wolfram Alpha computational engine and returns the result.
        Use the reactions to show more output or delete the output.
    Flags:2
        text:: Attempts to reply with a copyable plaintext version of the output.
    """
    loading_emoji = "<a:{}:{}>".format(ctx.bot.objects["emoji_loading"].name, ctx.bot.objects["emoji_loading"].id)

    temp_msg = await ctx.reply("Sending query to Wolfram Alpha, please wait. {}".format(loading_emoji))
    result = await get_query(ctx.arg_str, ctx.bot.objects["wolf_appid"])
    if not result:
        await ctx.bot.delete_message(temp_msg)
        await ctx.reply("Failed to get a response from Wolfram Alpha. If the problem persists, please contact support.")
        return
    if "queryresult" not in result:
        await ctx.bot.delete_message(temp_msg)
        await ctx.reply("Did not get a valid response from Wolfram Alpha. If the problem persists, please contact support.")
        return

    link = "[Display search on Wolfram]({})".format(build_web_url(ctx.arg_str))
    if not result["queryresult"]["success"] or result["queryresult"]["numpods"] == 0:
        desc = "Wolfram Alpha doesn't understand your query!\n Perhaps try rephrasing your question?\n{}".format(link)
        embed = discord.Embed(description=desc)
        embed.set_footer(icon_url=ctx.author.avatar_url, text="Requested by {}".format(ctx.author))
        await ctx.bot.delete_message(temp_msg)
        await ctx.reply(embed=embed)
        return

    if ctx.flags["text"]:
        fields = await pods_to_textdata(result["queryresult"]["pods"])
        embed = discord.Embed(description=link)
        embed.set_footer(icon_url=ctx.author.avatar_url, text="Requested by {}".format(ctx.author))
        await ctx.emb_add_fields(embed, fields)
        await ctx.bot.delete_message(temp_msg)
        out_msg = await ctx.reply(embed=embed)
        await ctx.offer_delete(out_msg)
        return

    important, extra = triage_pods(result["queryresult"]["pods"])

    data = (await pods_to_filedata(important))[0]
    output_data = [data]

    embed = discord.Embed(description=link)
    embed.set_footer(icon_url=ctx.author.avatar_url, text="Requested by {}".format(ctx.author))

    await ctx.bot.delete_message(temp_msg)
    out_msg = await ctx.reply(file_data=data, file_name="wolf.png", embed=embed)
    asyncio.ensure_future(ctx.offer_delete(out_msg))
   
    if extra:
        try:
            await ctx.bot.add_reaction(out_msg, ctx.bot.objects["emoji_more"])
        except discord.Forbidden:
            pass
        else:
            res = await ctx.bot.wait_for_reaction(message=out_msg,
                                                  user=ctx.author,
                                                  emoji=ctx.bot.objects["emoji_more"],
                                                  timeout=300)
            if res is None:
                try:
                    await ctx.bot.remove_reaction(out_msg, ctx.bot.objects["emoji_more"], ctx.me)
                except discord.NotFound:
                    pass
            elif res.reaction.emoji == ctx.bot.objects["emoji_more"]:
                temp_msg = await ctx.reply("Processing results, please wait. {}".format(loading_emoji))

                output_data[0].seek(0)
                output_data.extend(await pods_to_filedata(extra))
                try:
                    await ctx.bot.delete_message(out_msg)
                    await ctx.bot.delete_message(temp_msg)
                except discord.NotFound:
                    pass

                out_msgs = []
                for file_data in output_data[:-1]:
                    out_msgs.append(await ctx.reply(file_data=file_data, file_name="wolf.png"))
                out_msgs.append(await ctx.reply(file_data=output_data[-1], file_name="wolf.png", embed=embed))
                out_msg = out_msgs[-1]
                await ctx.offer_delete(out_msg, to_delete=out_msgs)

    for output in output_data:
        output.close()


def load_into(bot):
    bot.objects["wolf_appid"] = bot.bot_conf.get("WOLF_APPID")
