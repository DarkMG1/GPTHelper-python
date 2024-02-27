import discord

class EmbedBuilder:
    def __init__(self) -> None:
        self.footer = ""
        self.icon_url = ""
        self.fields = list()
        self.author = ""
        self.title = ""
        self.description = ""
        self.color = discord.Color.blue()
        self.url = ""
        self.timestamp = discord.utils.utcnow()

    def  settitle(self, title: str) -> 'EmbedBuilder':
        self.title = title
        return self

    def setdescription(self, description: str) -> 'EmbedBuilder':
        self.description = description
        return self

    def appenddescription(self, description: str) -> 'EmbedBuilder':
        self.description += description
        return self

    def setcolor(self, color: discord.Color) -> 'EmbedBuilder':
        self.color = color
        return self

    def seturl(self, url: str) -> 'EmbedBuilder':
        self.url = url
        return self
    
    def setauthor(self, name: str) -> 'EmbedBuilder':
        self.author = name
        return self
    
    def addfield(self, name: str, value: str, inline: bool = False) -> 'EmbedBuilder':
        self.fields.append(Field(name, value, inline))
        return self

    def build(self) -> discord.Embed:
        eb = discord.Embed(
            title=self.title,
            description=self.description,
            color=self.color,
            url=self.url,
            timestamp=self.timestamp
        )
        if self.author != "":
            eb.set_author(name=self.author)
        for field in self.fields:
            eb.add_field(name=field.name, value=field.value, inline=field.inline)
        if self.footer != "" and self.icon_url != "":
            eb.set_footer(text=self.footer, icon_url=self.icon_url)
        return eb

    def setfooter(self, text: str) -> 'EmbedBuilder':
        self.footer = text
        return self

    def seticonurl(self, icon_url: str) -> 'EmbedBuilder':
        self.icon_url = icon_url
        return self

    def black(self) -> 'EmbedBuilder':
        self.color = discord.Color.from_rgb(0,0,0)
        return self

class Field:
    def __init__(self, name: str, value: str, inline: bool = False) -> None:
        self.name = name
        self.value = value
        self.inline = inline

def geterrorembedbuilder(fieldname: str, fieldvalue: str) -> discord.Embed:
    eb  = getbaseembedbuilder()
    return (eb
            .settitle("Unavailable")
            .setdescription("Error has occurred. Please see reason below.")
            .addfield(fieldname, fieldvalue)
            .build())

def getnopermsembedbuilder() -> discord.Embed:
    eb = getbaseembedbuilder()
    return (eb
            .settitle("No Permission")
            .setdescription("You do not have permission to use this command.")
            .setcolor(discord.Color.red())
            .build())


def getbaseembedbuilder() -> EmbedBuilder:
    eb = EmbedBuilder()
    return (eb
            .setfooter('GPTHelper')
            .seticonurl("https://darkmg1.dev/logos/Dark%20Services%20Main%20Solid.png")
            .setauthor("GPTHelper"))