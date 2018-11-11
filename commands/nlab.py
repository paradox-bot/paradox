from paraCH import paraCH
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import urllib
import discord

cmds = paraCH()


nlab_url = "https://ncatlab.org{}"
search_target="https://ncatlab.org/nlab/search?query={}"

async def soup_site(target):
    async with aiohttp.ClientSession() as session:
        async with session.get(target, allow_redirects=False) as resp:
            text = await resp.read()
    return BeautifulSoup(text, 'html.parser')

async def search_page_parse(soup):
    in_title = []
    in_body = []
    header_soups = soup.find_all("h2")
    if "No pages contain" in header_soups[0].contents[0]:
        return ([],[])
    if len(header_soups) > 2:
        return None
    elif len(header_soups) == 2:
        in_title = results_parse(header_soups[0])
        in_body = results_parse(header_soups[1])
    elif len(header_soups) == 0:
        return ([],[])
    else:
        in_title = []
        in_body = results_parse(header_soups[0])
    return (in_title, in_body)


def results_parse(soup):
    links = soup.nextSibling.nextSibling.findAll("a")
    results = ( (a.contents[0], a.attrs["href"]) for a in links)
    return results

async def search_for(string):
    soup = await soup_site(search_target.format(urllib.parse.quote_plus(string)))
    if not "Search results" in soup.find("title").contents:
        return None
    return await search_page_parse(soup)


@cmds.cmd("nlab",
          category="Maths",
          short_help="Searches the nLab",
          aliases=["nlablink", "nl"])
async def cmd_nlab(ctx):
    """
    Usage:
        {prefix}nlab <search>
        {prefix}nlablink <page name>
    Description:
        If used as nlab, searched the nLab for the provided search string.
        Currently only provides the top 10 results of each type.
        If used as nlablink, provides the direct link to the nlab page with the given name.
        This does not check whether the page exists.
    Examples:
        {prefix}nlablink category
        {prefix}nlab categorical group
    """
    direct_page = nlab_url.format("/nlab/show/{}".format(urllib.parse.quote_plus(ctx.arg_str)))
    if ctx.used_cmd_name == "nlablink":
        await ctx.reply(direct_page if ctx.arg_str else nlab_url[:-2])
        return

    if not ctx.arg_str:
        await ctx.reply("Give me something to search for!")
        return

    out_msg = await ctx.reply("Searching, please wait.")
    url = search_target.format(urllib.parse.quote_plus(ctx.arg_str))


    soup = await soup_site(url)
    direct_soup = await soup_site(direct_page)
    direct_found = False if not direct_soup.find("title") or "Page not found" in direct_soup.find("title").contents[0] else True
    direct_str = "\nDirect page found at: [{}]({})".format(ctx.arg_str, direct_page) if direct_found else ""

    if not "Search results" in soup.find("title").contents[0]:
        await ctx.bot.edit_message(out_msg, "Nlab directed us to this page which I don't understand:\n{}".format(soup.find("a").attrs["href"]))
        return
    parsed = await search_page_parse(soup)
    if not parsed:
        await ctx.bot.edit_message(out_msg, "I don't understand the search results. Read them yourself at:\n{}".format(url))
        return
    in_title, in_body = parsed
    emb_fields = []
    if in_title:
        in_title = list(in_title)
        in_title_str = "\n".join(["[{}]({})".format(link[0], nlab_url.format(link[1])) for link in in_title][:8])
        emb_fields.append(("{} result{} where query appeared in title".format(len(in_title), "" if len(in_title) == 1 else "s"), in_title_str, 0))
    if in_body:
        in_body = list(in_body)
        in_body_str = "\n".join(["[{}]({})".format(link[0], nlab_url.format(link[1])) for link in in_body][:8])
        emb_fields.append(("{} result{} where query appeared in body".format(len(in_body), "" if len(in_body) == 1 else "s"), in_body_str, 0))
    if not in_title and not in_body:
        await ctx.bot.edit_message(out_msg, "No results found at:\n{}".format(url))
        return
    embed = discord.Embed(title="Search results for {}".format(ctx.arg_str), description="From {}{}".format(url, direct_str), color=discord.Colour.light_grey())
    await ctx.emb_add_fields(embed, emb_fields)
    print(embed.to_dict())
    await ctx.bot.edit_message(out_msg, new_content=" ", embed=embed)
