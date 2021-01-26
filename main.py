import discord
from discord.ext import commands
import os
from piazza_api import Piazza
import html2text
import datetime
import pytz
from pylatexenc.latex2text import LatexNodes2Text
from keep_alive import keep_alive
from matplotlib import pyplot as plt
import math

keep_alive()

intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix='!', intents=intents)
TOKEN = os.environ.get('TOKEN')

p = Piazza()
p.user_login(os.environ.get('email'), os.environ.get('password'))

user_pf = p.get_user_profile()
courses = {'esc180': 'kemwxod4vln1xz', 'phy180' : 'kek6nj9ihcd2nm', 'civ102': 'ketdyx1wdd4mr', 'esc194': 'kf2l9rqyyta40b', 'esc101': 'kf2phey5e79751', 'esc102':'kjqcaz1xuqx37w', 'mse160': 'kjp0xjmwaok3gp', 'ece159':'kjp6lgqbe3e3cj', 'mat185': 'kjspjan3id620h', 'esc195':'kjsvvnay2lzdp', 'esc190': 'kjt3ii0940y6p'}

pinned_posts = []
del_message = ''

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # if message.author.id == 715581235170377828:
    #     await message.add_reaction('👶')

    if message.content.startswith('p@ pinned'):
        await pinned(message)
    
    if message.content.startswith('p@ get'):
        await get(message)
        
    if message.content.startswith('p@ search'):
        await search(message)

    if message.content.startswith('r@ help'):
        await message.channel.send(">>> __Rigour commands__:\n**r@ getrole** - get verified role on the server\n**r@ admin (number)** - view most admin pings by user in past (number) days\n**r@ maksnipe** - snipe Mak's latest deleted message\n__Piazza commands__:\n**p@ search (course) (query)** - return a post based on a query\n**p@ get (course) (post id)** - return a post based on the post id\n**p@ pinned (course)** - return pinned posts in a specific course\n**p@ reply (course) (post id)** - return replies for a specific post\n**p@ suggestion (suggestion)** - let us know how to improve the bot\n**p@ report (report)** - report any issues with the bot")
   
    if message.content.startswith('p@ reply'):
        await reply(message)

    if message.content.startswith('p@ suggestion'):
        user_message = message.content[14:]
        with open('suggestions.txt', 'a') as suggestions:
            suggestions.write(f"Suggested: {datetime.datetime.now()}\n")
            suggestions.write(f"\t{user_message}\n\n")
        suggestions.close()
        await message.channel.send('Suggestion submitted. Thank you!')

    if message.content.startswith('p@ report'):
        user_message = message.content[10:]
        with open('reports.txt', 'a') as reports:
            reports.write(f"Reported: {datetime.datetime.now()}\n")
            reports.write(f"\t{user_message}\n\n")
        reports.close()
        await message.channel.send('Report submitted. Thank you!')

    if message.content.startswith('r@ getrole'):
        await message.author.send("To get the verified role, please sent me your utorid.")

    if isinstance(message.channel, discord.channel.DMChannel) and message.author != client.user:
        await dm_role(message)

    server = client.get_guild(701521452662390854)
    role = discord.utils.get(server.roles, name="Admin").id
    role_id = f'<@&{role}>'

    if role_id in message.content:
        admin_count(message.author)

    if message.content.startswith('r@ admin'):
        msg = message.content.split()
        try:
          limit = int(msg[2])
          check_admin_count(limit)
          await message.channel.send(file=discord.File('plot.png'))
        except:
          await message.channel.send("Please submit a valid number.")

    if message.content.startswith('r@ maksnipe'):
      if del_message:
        await message.channel.send(f'Mak said: {del_message}')

@client.event
async def on_reaction_add(reaction, user):
    if user == client.user:
        return

    server = client.get_guild(701521452662390854)
    role = discord.utils.get(server.roles, name="verified")
    member = server.get_member(int(user.id))
    msg = '>>> **Do you agree to the following:**\n1) I have read and agree to follow the rules listed in the Code of Behaviour of Academic Matters.\n2) I have read and agree to follow the rules listed in the #intro-and-code-of-conduct channel.\n3) The utorid'
    if msg in reaction.message.content and reaction.emoji == '👍':
        await member.add_roles(role)
        await reaction.message.delete()
        await reaction.message.channel.send('Role added.')
        utorid = reaction.message.content[246:]
        a = utorid.find(' ')
        utorid = utorid[:a]
        with open('utorids.txt', 'a') as utorids:
            utorids.write(f'{user}\n{utorid}\n')
        utorids.close()
    elif msg in reaction.message.content and reaction.emoji == '👎':
        await reaction.message.delete()
        await reaction.message.channel.send('You will be restricted from all academic channels in the EngSci 2T4 server.')

@client.event
async def on_member_join(member: discord.Member):
    await member.send("Welcome to the EngSci 2T4 server!\nIf you are a EngSci 2T4 student, send me your utorid to get the verified role and gain access to the academic channels!")

@client.event
async def on_member_remove(member: discord.Member):
    remove_utorid(member)
    return

@client.event
async def on_message_delete(message):
  global del_message
  if message.author.id == 715581235170377828:
    del_message = message.content

@client.command()
async def pinned(message):
    user_message = message.content.split(' ')
    if user_message[2] not in courses:
      await message.channel.send(f"{user_message[2]} could not be accessed.")
    else:
      pinned_posts = get_pinned_posts(user_message[2])
      pinned_posts = format_pinned_message(pinned_posts, user_message[2])
      if len(pinned_posts) > 2000:
          post = split_post(user_message)
          try:
              for elem in post:
                  await message.channel.send(elem)
          except:
              await message.channel.send("List too long. Please view in browser.")
      else:
          await message.channel.send(pinned_posts)

@client.command()
async def get(message):
    user_message = message.content.split(' ')
    if user_message[2] not in courses:
      await message.channel.send(f"{user_message[2]} could not be accessed.")
    else:
      post = get_message(user_message[2], user_message[3])
      if type(post) == list and len(post) != 1 and len(post) != 0:
          for elem in post:
              if len(elem) > 2000:
                  try:
                      for elem2 in elem:
                          await message.channel.send(elem2)
                  except:
                      await message.channel.send("Post too long. Please view in browser.")
                      break
              else:
                  try:
                      await message.channel.send(elem)
                  except:
                      pass
      else:
          if len(post[0]) > 2000:
              post[0] = split_post(post[0])
              try:
                  for elem in post[0]:
                      await message.channel.send(elem)
              except:
                  await message.channel.send("Post too long. Please view in browser.")
          elif type(post) == str:
            try:
                  await message.channel.send(post)
            except:
                  pass
          else:
              try:
                  await message.channel.send(post[0])
              except:
                  pass

@client.command()
async def search(message):
    user_message = message.content
    user_message = [user_message[:9]] + [user_message[10:16]] + [user_message[17:]]
    if user_message[1] not in courses:
      a = user_message[1].find(' ')
      if a != -1:
        await message.channel.send(f"{user_message[1][:a]} could not be accessed.")
      else:
        await message.channel.send(f"{user_message[1]} could not be accessed.")
    else:
      post = search_post(user_message[1], user_message[2])
      if type(post) == list:
          for elem in post:
              if len(elem) > 2000:
                  elem = split_post(elem)
                  try:
                      for elem2 in elem:
                          await message.channel.send(elem2)
                  except:
                      await message.channel.send("Post too long. Please view in browser.")
              else:
                  try:
                      await message.channel.send(elem)
                  except:
                      pass
      else:
          if len(post) > 2000:
              post = split_post(post)
              try:
                  for elem in post:
                      await message.channel.send(elem)
              except:
                  await message.channel.send("Post too long. Please view in browser.")
          else:
              await message.channel.send(post)

@client.command()
async def reply(message):
    user_message = message.content.split(' ')
    course = p.network(courses[user_message[2]])
    if user_message[2] not in courses:
      await message.channel.send(f"{user_message[3]} could not be accessed.")
    else:
      try:
          post = course.get_post(user_message[3])
          post = get_response(post)
          if len(post) != 0 and len(post) != 1:
              for elem in post:
                  if len(elem) > 2000:
                      elem = split_post(elem) 
                      try:
                          for elem2 in elem:
                              await message.channel.send(elem2)
                      except:
                          await message.channel.send("Reponse(s) too long. Please view in browser.")
                  else:
                      try:
                          await message.channel.send(elem)
                      except:
                          pass
          else:
              if len(post[0]) > 2000:
                  post[0] = split_post(post[0]) 
                  try:
                      for elem in post[0]:
                          await message.channel.send(elem)
                  except:
                      await message.channel.send("Reponse(s) too long. Please view in browser.")
              else:
                  await message.channel.send(post[0])
      except:
          await message.channel.send(f'Could not access post {user_message[3]}.')

@client.command()
async def dm_role(message):
  user_message = message.content
  name = user_message
  duplicate = check_duplicates(user_message)
  user_message = check_utorid(user_message)
  if user_message:
      if duplicate:
          server = client.get_guild(701521452662390854)
          role = discord.utils.get(server.roles, name="verified")
          member = server.get_member(int(message.author.id))
          await client.wait_until_ready()
          if member:
              if role in member.roles:
                  await message.channel.send('You already have this role.')
              else:
                  msg = await message.channel.send(f'>>> **Do you agree to the following:**\n1) I have read and agree to follow the rules listed in the Code of Behaviour of Academic Matters.\n2) I have read and agree to follow the rules listed in the #intro-and-code-of-conduct channel.\n3) The utorid {name} belongs to you.\n**React with 👍 if you agree or 👎 if you disagree**')                   await msg.add_reaction('👍')                  wait msg.add_reaction('👎')            se:
                 it message.channel.send('You are not in the server.')
         e:
             it message.channel.send('This utorid is already in use. If you believe this is a mistake, please contact one of the admins.')
     e:
         it message.channel.send('The given utorid could not be found.')

def search_post(course, search):
    try:
      post = p.network(courses.get(course.lower())).search_feed(search)
    except:
      pass
    try:
        post = post[0]['nr']
        post = get_message(course, post)
        return post
    except:
        return f'No posts were found using the query "{search}".'

def format_post(post):
    layer1 = post['history']
    replies = ''
    try:
        replies = post['children'][0]['type']
    except:
        pass
    message = layer1[0]['content']
    try:
        title = layer1[0]['subject']
        cid = post['nr'] 
        title += f" - ID: {cid}" 
    except:
        pass

    html_dict = {'&#39;': "'", '&#60;': '<', '&#62;': '>', '&#38;': '&', '&#34;': '"', '&#160;': '', '&#43;': '+'}
    for elem in html_dict.keys():
        message = message.replace(elem, html_dict[elem])
        title = title.replace(elem, html_dict[elem])

    if message.find('<img src="') != -1:
        message = message.replace('<img src="', '\0\0')
        message = message.replace('alt="', '\0\0')
        message = message.replace(' />', '\0\0')
        message = message.split('\0\0')
        for i in range(len(message)):
            if i % 3 == 0:
                message[i] = cleanhtml(message[i])
                message[i] = cleanlatex(message[i])
            elif i % 3 == 1:
                message[i] = message[i][:-2]
                message[i] = f'https://piazza.com{message[i]}'
            else:
                message[i] = ' '
        try:
            while True:
                message.remove(' ')
        except ValueError:
            pass
        
    else:
        message = cleanlatex(message)
        message = [cleanhtml(message)]
    
    if title:
        message[0] = f'**{title}**\n{message[0]}'
    if replies != 'followup' and replies != '':
        i = len(message[-1])
        while(message[-1][i-1:] == '\n'):
            message[-1] = message[-1][:-2]
            i -= 2
        message[-1] = f'{message[-1]}\n> Replies detected. To see them, respond with: ``p@ reply (course) (post id)``'
    
    return message

def cleanhtml(raw_html):
  cleantext = html2text.html2text(raw_html)
  return cleantext

def cleanlatex(raw_latex):
    cleantext = LatexNodes2Text().latex_to_text(raw_latex)
    return cleantext

def get_message(course, cid):
    try:
        post = p.network(courses.get(course.lower())).get_post(cid)
        post = format_post(post)
    except:
        return f'Post {cid} not found'
    return post

def pinned_post(post):
    if post.find('#pin') != -1:
        return True
    return False

def format_pinned_message(message, course):
    if len(message) == 1:
        string = '**The following message has been pinned in the last month in ' + course + ':**\n'
    elif len(message) > 1:
        string = '**The following messages have been pinned in the last month in ' + course + ':**\n'
    else:
        string = 'No messages have been pinned in the last month in ' + course + '.'
    for elem in message:
        string += elem
        string += '\n'
    return string

def get_pinned_posts(course):
    all_posts = p.network(courses.get(course.lower())).iter_all_posts()
    pinned_posts = []
    while True:
        try:
            post = next(all_posts)
            post1 = format_post(post)
            if check_time(post) == True:
                i = 3
                title = post1[0][2]
                while(post1[0][i-1] != '*' and post1[0][i] != '*'):
                    title += post1[0][i]
                    i += 1
                for elem in post1:
                    if pinned_post(elem) == True:
                        pinned_posts.append(title)
            else:
                break 
        except:
            break
    return pinned_posts

def split_post(post):
    punctuation_array = ['.', '?', '!']
    prefix_array = ['Mr', 'Mrs', 'Ms', "Dr"]
    i = 2000
    while(post[i] not in punctuation_array):
        if post[i-3:i-1] in prefix_array or post[i-4:i-1] in prefix_array:
            i -= 2
        i -= 1
    post = [post[:i+1]] + [post[i+1:]]
    return post

def format_time(t):
    t = t.replace('Z','')
    t = t.replace('T', ' ')
    t = t.replace(':', ' ')
    t = t.replace('-', ' ')
    t = t.split()
    return t

def check_time(post):
    cur_time = str(datetime.datetime.now())
    cur_time = format_time(cur_time)
    post_time = post['created']
    post_time = format_time(post_time)
    if post_time[0] == cur_time[0]:
        if post_time[1] == cur_time[1]:
            if int(cur_time[2]) - int(post_time[2]) < 30:
                return True
            else:
                return False
        else:
            if int(cur_time[1]) - int(post_time[1]) > 1:
                return False
            else:
                if int(cur_time[1]) + int(post_time[1]) < 30:
                    return True
                else:
                    return False
    elif int(cur_time[0]) - int(post_time[0]) == 1:
      if cur_time[1] == '01' and post_time[1] == '12':
        if int(cur_time[2]) - int(post_time[2]) <= 0:
          return True
        return False
      return False
    else:
      return False

def get_response(post):
    try:
        response = format_post(post['children'][0])
        response_type = post['children'][0]['type']
    except:
        return 'Post has no responses.'
    try:
      i_response = format_post(post['children'][1])
    except:
      i_response = None
    message = format_response(response, response_type, i_response)
    return message

def format_response(ans1, r_type, ans2):
    if ans2 == None:
        if r_type == 's_answer':
            ans1[0]= '**Student Answer:**\n' + ans1[0]
        else:
            ans1[0]= '**Instructor Answer:**\n' + ans1[0]
        return ans1
    else:
        ans1[0]= '**Student Answer:**\n' + ans1[0]
        ans2[0]= '**Instructor Answer:**\n' + ans2[0]
        return ans1 + ans2

def check_utorid(utorid):
    with open("EngSci_Utorid.txt") as f: text = f.read().split(' ')
    if utorid in text:
        return True
    return False

def check_duplicates(utorid):
    with open("utorids.txt") as f: text = f.read().split('\n')
    if utorid in text:
        return False
    return True

def remove_utorid(name):
  name = str(name) + '\n'
  with open('utorids.txt', 'r') as f:
    lines = f.readlines()
  with open('utorids.txt', 'w') as f:
    for i in range(0, len(lines), 2):
      if lines[i] != name:
        f.write(lines[i])
        f.write(lines[i+1])

def admin_count(user):
    with open('admin.txt', 'a') as f:
      tz = pytz.timezone('EST')
      timestamp = str(datetime.datetime.now(tz=tz))
      f.write(f'{timestamp} {user}\n')

def check_admin_count(limit):
  with open('admin.txt', 'r') as f:
    pings = check_admin_time(limit)
    pings_set = set(pings)
    data = {}
    x_data = []
    y_data = []
    for person in pings_set:
      data[person] = pings.count(person)
    
    data = dict(sorted(data.items(), key=lambda item: item[1]))
    keys = list(data.keys())
    
    if len(keys) < 5:
      length = len(keys)
    else:
      length = 5

    for i in range(length):
      x_data.append(keys[len(keys)-1-i])
      y_data.append(data[keys[len(keys)-1-i]])

    plt.bar(x_data, y_data, align='center', alpha=0.5)
    plt.xticks(x_data, x_data)
    if length != 0:
      yint = range(0, math.ceil(max(y_data))+1)
    else:
      yint = range(0, 1)
    plt.yticks(yint)
    plt.ylabel('Number of pings', weight = 'bold')
    plt.xlabel('Users', weight = 'bold')
    plt.title(f'Most Admin Pings by User in the Past {limit} Days', weight = 'bold')
    plt.savefig('plot.png')
    plt.close()

def check_admin_time(limit):
  tz = pytz.timezone('EST')
  cur_time = str(datetime.datetime.now(tz=tz))[:10]
  num_pings = []
  with open('admin.txt', 'r') as f:
    lines = f.readlines()
    for i in range(len(lines)-1, -1, -1):
      timestamp = lines[i][:10]
      num_days = (int(cur_time[:4]) - int(timestamp[:4]))*365 + (int(cur_time[5:7]) - int(timestamp[5:7]))*30 + int(cur_time[8:10]) - int(timestamp[8:10])
      if num_days > limit:
        return num_pings
      num_pings.append(lines[i][33:-6])
    return num_pings

client.run(TOKEN)
