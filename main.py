import discord
import os
from piazza_api import Piazza
import sched, time
import html2text
import datetime
from pylatexenc.latex2text import LatexNodes2Text
from keep_alive import keep_alive

keep_alive()
TOKEN = os.environ.get('TOKEN')
client = discord.Client()

p = Piazza()
p.user_login(os.environ.get('email'), os.environ.get('password'))

user_pf = p.get_user_profile()
courses = {'esc180': 'kemwxod4vln1xz', 'phy180' : 'kek6nj9ihcd2nm', 'civ102': 'ketdyx1wdd4mr', 'esc194': 'kf2l9rqyyta40b', 'esc101': 'kf2phey5e79751', 'esc102':'kjqcaz1xuqx37w', 'mse160': 'kjp0xjmwaok3gp', 'ece159':'kjp6lgqbe3e3cj', 'mat185': 'kjspjan3id620h', 'esc195':'kjsvvnay2lzdp', 'esc190': 'kjt3ii0940y6p'}

pinned_posts = []

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('p@ pinned'):
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
    
    if message.content.startswith('p@ get'):
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
        
    if message.content.startswith('p@ search'):
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

    if message.content.startswith('r@ help'):
        await message.channel.send(">>> **p@ search (course) (query)** - to return a post based on a query\n**p@ get (course) (post id)** - to return a post based on the post id\n**p@ pinned (course)** - to return pinned posts in a specific course\n**p@ reply (course) (post id)** - to return replies for a specific post\n**p@ suggestion (suggestion)** - let us know how to improve the bot\n**p@ report (report)** - report any issues with the bot")
   
    if message.content.startswith('p@ reply'):
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
                              for elem2 in elem2:
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

client.run(TOKEN)