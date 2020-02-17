import psycopg2
import sys, tempfile, os
from subprocess import call

'''
implementation of "luhmann's second brain" or "luhmann's slip box"

"Early in his academic career, Luhmann realized that a note was only as valuable
as its context – its network of associations, relationships, and connections to other information."
references:
    https://praxis.fortelabs.co/how-to-take-smart-notes/
    https://www.buildingasecondbrain.com/
    https://www.amazon.com/gp/product/B06WVYW33Y/ref=as_li_tl?ie=UTF8&tag=fortelabs07-20&camp=1789&creative=9325&linkCode=as2&creativeASIN=B06WVYW33Y&linkId=3ee89186dc2ad427b5e43936fe48cb39

    the luhmann notes, online:
    http://ds.ub.uni-bielefeld.de/viewer/search/-/MD_AUTHOR_UNTOKENIZED:%22Luhmann%2CU005C+Niklas%22/1/-/-/


sample project to begin note-taking:
    https://github.com/VGraupera/1on1-questions
    https://plus.maths.org/content/ramanujan
    https://umanitoba.ca/admin/human_resources/change/media/the-art-of-powerful-questions.pdf
    https://www.quantamagazine.org/the-map-of-mathematics-20200213/
    https://en.wikipedia.org/wiki/Riemann_zeta_function


commands:
insert
edit
create-schema

note attributes:
title
body
id
- ids increase sequentially forever
- id is a parent topic
- id has _no importance_ other than having the quality of being a top-level category and is the
  parent of a series of sub-ids. It is not an organizer of any kind.
- ideas are thematically unlimited and can be infinitely extended in any direction 
branch
- references a foreign key parent_id to affiliate it with a parent
- is a instance of a parent idea (ie, if "genocide" is a parent topic, then "holocaust" would be the title of a sub id)
id reference
- a branch is a linked list of ideas that go off a parent topic

goals:
- a python script that can create notes
- runs on sql
- a web server that can be set up at any time and connect to a db of luhmann notes
  web server does some visualization with a graph of parent topics

TODO: going to try this with a docker db initally. Need a way to persist between iterations
    maybe I can just save a sql file and run a sql binary when I need to
'''

# idk if this is useful
class Note:
    # if parent_id == None, this is a top-level idea
    def __init__(self, id, text, parent_id=None, siblings=[]):
        self.id = id
        self.text = text
        self.parent_id = parent_id
        self.siblings = siblings


# global DB connection
conn = psycopg2.connect(host="localhost",database="luhman", user="postgres", password="luhman")

# we will probably need to alter the size of "text" later 
def create_schema():
    # connect to DB
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE idea (
    id int NOT NULL,
    title varchar(255),
    text varchar(255),
    siblings varchar(255),
    PRIMARY KEY(id)
    )
    ''')
    
    cur.execute('''
    CREATE TABLE sub_idea (
    id int NOT NULL,
    title varchar(255),
    text varchar(255),
    siblings varchar(255),
    parent_id int NOT NULL,
    PRIMARY KEY(id),
    FOREIGN KEY(parent_id) REFERENCES idea(id)
    )
    ''')
    
    conn.commit()
    conn.close()

def get_next_id(table_name):
    cmd = 'SELECT id FROM {} ORDER BY id DESC LIMIT 1;'.format(table_name)
    cur = conn.cursor()
    cur.execute(cmd)

    # just pop off the top of the list
    val = cur.fetchone()

    conn.commit()
    if val == None or len(val) == 0:
        return 1

    return val[0] + 1

# "siblings" dumps a python list as a string into the column so we can turn it into python later
# this is "bad sql" and will almost certainly bite me in the ass later 
# There has to be a better way to do this 
def insert_idea(id, title, body, siblings):
    cmd = 'INSERT INTO idea (id,title,text, siblings) VALUES ({},\'{}\',\'{}\',\'{}\');'.format(id, title, body, siblings)
    cur = conn.cursor()
    cur.execute(cmd)
    conn.commit()

def insert_sub_idea(id, parent_id, title, body, siblings):
    cmd = 'INSERT INTO sub_idea (id,parent_id,title,text,siblings) VALUES ({},\'{}\',\'{}\',\'{}\',\'{}\');'.format(id, parent_id, title, body, siblings)
    cur = conn.cursor()
    cur.execute(cmd)
    conn.commit()

def find_idea(table, input):
    cmd = 'SELECT * FROM {} WHERE title LIKE \'%{}%\';'.format(table, input)
    cur = conn.cursor()

    cur.execute(cmd)
    conn.commit()
    return cur.fetchall()

def update_field(table, field, new, id):
    cmd = 'UPDATE {} SET {}=\'{}\' WHERE id={};'.format(table, field, new, id)
    cur = conn.cursor()
    cur.execute(cmd)
    conn.commit()

# from https://stackoverflow.com/questions/6309587/call-up-an-editor-vim-from-a-python-script
def open_vim(text):

    EDITOR = os.environ.get('EDITOR','vim') #that easy!

    initial_message = text # if you want to set up the file somehow

    with tempfile.NamedTemporaryFile(suffix=".tmp") as tf:
        tf.write(initial_message.encode())
        tf.flush()
        call([EDITOR, tf.name])

        # do the parsing with `tf` using regular File operations.
        # for instance:
        tf.seek(0)
        edited_message = tf.read()
        return str(edited_message.decode()).strip("\n")

'''
command line parsing and runtime
'''
if len(sys.argv) == 1:
    print('''
    Provide a command:

    create-schema
     - creates the simple idea schema. Not idempotent. who cares

    new 
     - open the idea prompt
    
    edit 
     - open the edit prompt

    new-sub
     - open the sub-idea command prompt
    ''')

cmd = sys.argv[1]

if cmd == "create-schema":
    create_schema()
elif cmd == "new":
    # get next id to create and then open prompt
    id = get_next_id("idea")
    title = input("Title: ")
    text = open_vim("")

    # search for siblings
    more_siblings = ""
    siblings = []
    while more_siblings != 'n':
        more_siblings = input("Add a reference to a sibling? (y/n) ")
        if more_siblings == 'y':
            search = input("Search for a term to find a sibling topic: ")
            vals = find_idea("idea", search)
            if len(vals) == 0:
                print('no ideas found for search term "{}", try a different search.'.format(search))
                continue

            for i,val in enumerate(vals):
                print("{}: {}".format(i, val))
            selection = input("select index: ")

            selected = vals[int(selection)]
            print('Added topic "{}" as a sibling topic.'.format(selected[1]))
            siblings.append(selected[0])
        elif more_siblings == 'n':
            break
        else:
            print('Enter "y" or "n", you imbecile')


    insert_idea(id, title, text, siblings)


elif cmd == "edit":
    table = ""
    while table != "sub_idea" and table != "idea":
        table = input('Update child or parent table? Enter "idea" or "sub_idea": ')

    # TODO: switch to toggle between sub-idea table or parents
    # TODO-TODO: refactor it so it's all one big table and relations can be infinitely nested
    # request the parent idea; use "like" to search ideas
    # then ask to edit the name, and open a nifty text editor
    # for the text body
    # everything is mutable
    search = input("Input idea you want to edit: ")
    vals = find_idea(table, search)
    if len(vals) == 0:
        print('no ideas found for search term "{}", exiting...'.format(search))
        sys.exit(1)

    for i,val in enumerate(vals):
        print("{}: {}".format(i, val))
    selection = input("select index: ")

    selected = vals[int(selection)]
    print(selected)

    edit_title = ""
    while edit_title != 'y' and edit_title != 'n':
        edit_title = input("Edit title? (y/n) ")
    
    if edit_title == 'y':
        new_title = input("Current title: {}. Enter new title: ".format(selected[1]))
        update_field(table, "title", new_title, selected[0])
    
    edit_body = ""
    while edit_body != 'y' and edit_body != 'n':
        edit_body = input("Edit body? (y/n) ")
    
    if edit_body == 'y':
        new_text = open_vim(selected[2])
        update_field(table, "text", new_text, selected[0])

    edit_siblings = ""
    while edit_siblings != 'y' and edit_siblings != 'n':
        edit_siblings = input("Edit siblings? (y/n) ")
    
    if edit_siblings == 'y':
        # write a syntactically correct python list or woe fucking betide you my friend
        # manual DB updates lurk here. See comment on this method declaration
        new_siblings = open_vim(selected[3])
        update_field(table, "siblings", new_siblings, selected[0])


    
elif cmd == "new-sub":
    search = input("Input idea to select as a parent: ")
    vals = find_idea("idea", search)
    if len(vals) == 0:
        print('no ideas found for search term "{}", exiting...'.format(search))
        sys.exit(1)

    for i,val in enumerate(vals):
        print("{}: {}".format(i, val))
    selection = input("select index: ")

    selected = vals[int(selection)]
    parent_id = selected[0]

    id = get_next_id("sub_idea")

    title = input("Title: ")
    text = open_vim("")

    # search for siblings
    more_siblings = ""
    siblings = []
    while more_siblings != 'n':
        more_siblings = input("Add a reference to a sibling? (y/n) ")
        if more_siblings == 'y':
            search = input("Search for a term to find a sibling topic: ")
            vals = find_idea(table, search)
            if len(vals) == 0:
                print('no ideas found for search term "{}", try a different search.'.format(search))
                continue

            for i,val in enumerate(vals):
                print("{}: {}".format(i, val))
            selection = input("select index: ")

            selected = vals[int(selection)]
            print('Added topic "{}" as a sibling topic.'.format(selected[1]))
            siblings.append(selected[0])
        elif more_siblings == 'n':
            break
        else:
            print('Enter "y" or "n", you imbecile')


    insert_sub_idea(id, parent_id, title, text, siblings)
else:
    print('command "{}" not recognized; exiting.'.format(cmd))

# close global conn
conn.close()