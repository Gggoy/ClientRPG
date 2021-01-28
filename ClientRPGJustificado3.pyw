# import all the required modules 
import socket 
import threading 
from tkinter import *
from tkinter import font 
from tkinter import ttk 
import random
from colour import Color
import time
from tkinter.colorchooser import *
import sys
import re
import pickle

red=Color('#ff0000')
violet=Color('#ff00ff')
colors = list(red.range_to(violet,50))
colors=colors+list(violet.range_to(red,50))
namer=''

__all__ = ['TextWrapper', 'wrap', 'fill', 'dedent', 'indent', 'shorten']

_whitespace = '\t\n\x0b\x0c\r '

def justify(words, width):
    if len(words)==width:
        return(words)
    line = re.split("(\s+)",words)
    if line[0]=='':
        line.pop(0)
    i=0
    while True:
            for u in range(1,len(line)):
                if i==width-len(words):
                    corrigida=''
                    for elemen in line:
                        corrigida+=elemen
                    return(corrigida)
                elem=line[u]
                if elem.replace(' ','')=='' and line[u+1]!='>' and line[u-1]!='>':
                    line[u]+=" "
                    i+=1
            if i==0:
                while True:
                    if i==width-len(words):
                            corrigida=''
                            for elemen in line:
                                corrigida+=elemen
                            return(corrigida)
                    i+=1
                    line.append(' ')
class TextWrapper:
    unicode_whitespace_trans = {}
    uspace = ord(' ')
    for x in _whitespace:
        unicode_whitespace_trans[ord(x)] = uspace
    word_punct = r'[\w!"\'&.,?]'
    letter = r'[^\d\W]'
    whitespace = r'[%s]' % re.escape(_whitespace)
    nowhitespace = '[^' + whitespace[1:]
    wordsep_re = re.compile(r'''
        ( # any whitespace
          %(ws)s+
        | # em-dash between words
          (?<=%(wp)s) -{2,} (?=\w)
        | # word, possibly hyphenated
          %(nws)s+? (?:
            # hyphenated word
              -(?: (?<=%(lt)s{2}-) | (?<=%(lt)s-%(lt)s-))
              (?= %(lt)s -? %(lt)s)
            | # end of word
              (?=%(ws)s|\Z)
            | # em-dash
              (?<=%(wp)s) (?=-{2,}\w)
            )
        )''' % {'wp': word_punct, 'lt': letter,
                'ws': whitespace, 'nws': nowhitespace},
        re.VERBOSE)
    del word_punct, letter, nowhitespace
    wordsep_simple_re = re.compile(r'(%s+)' % whitespace)
    del whitespace
    sentence_end_re = re.compile(r'[a-z]'           
                                 r'[\.\!\?]'         
                                 r'[\"\']?'           
                                 r'\Z')               

    def __init__(self,
                 width=70,
                 initial_indent="",
                 subsequent_indent="",
                 expand_tabs=True,
                 replace_whitespace=False,
                 fix_sentence_endings=False,
                 break_long_words=False,
                 drop_whitespace=False,
                 break_on_hyphens=True,
                 tabsize=8,
                 *,
                 max_lines=None,
                 placeholder=' [...]'):
        self.width = width
        self.initial_indent = initial_indent
        self.subsequent_indent = subsequent_indent
        self.expand_tabs = expand_tabs
        self.replace_whitespace = replace_whitespace
        self.fix_sentence_endings = fix_sentence_endings
        self.break_long_words = break_long_words
        self.drop_whitespace = drop_whitespace
        self.break_on_hyphens = break_on_hyphens
        self.tabsize = tabsize
        self.max_lines = max_lines
        self.placeholder = placeholder

    # -- Private methods -----------------------------------------------

    def _munge_whitespace(self, text):
        if self.expand_tabs:
            text = text.expandtabs(self.tabsize)
        if self.replace_whitespace:
            text = text.translate(self.unicode_whitespace_trans)
        return text


    def _split(self, text):
        if self.break_on_hyphens is True:
            chunks = self.wordsep_re.split(text)
        else:
            chunks = self.wordsep_simple_re.split(text)
        chunks = [c for c in chunks if c]
        return chunks

    def _fix_sentence_endings(self, chunks):
        i = 0
        patsearch = self.sentence_end_re.search
        while i < len(chunks)-1:
            if chunks[i+1] == " " and patsearch(chunks[i]):
                chunks[i+1] = "  "
                i += 2
            else:
                i += 1

    def _handle_long_word(self, reversed_chunks, cur_line, cur_len, width):
        if width < 1:
            space_left = 1
        else:
            space_left = width - cur_len
        if self.break_long_words:
            cur_line.append(reversed_chunks[-1][:space_left])
            reversed_chunks[-1] = reversed_chunks[-1][space_left:]
        elif not cur_line:
            cur_line.append(reversed_chunks.pop())

    def _wrap_chunks(self, chunks):
        lines = []
        if self.width <= 0:
            raise ValueError("invalid width %r (must be > 0)" % self.width)
        if self.max_lines is not None:
            if self.max_lines > 1:
                indent = self.subsequent_indent
            else:
                indent = self.initial_indent
            if len(indent) + len(self.placeholder.lstrip()) > self.width:
                raise ValueError("placeholder too large for max width")
        chunks.reverse()

        while chunks:
            cur_line = []
            cur_len = 0
            if lines:
                indent = self.subsequent_indent
            else:
                indent = self.initial_indent
            width = self.width - len(indent)
            if self.drop_whitespace and chunks[-1].strip() == '' and lines:
                del chunks[-1]

            while chunks:
                if '\n' in chunks[-1]:
                    chunks.pop()
                    chunks.append('\j'+' -*- '*10)
                elif '\k' in chunks[-1] and not '\\\k' in chunks[-1]:
                        yob=chunks[-1].split('\k')
                        chunks.pop()
                        if yob[1]!='':
                            chunks.append(yob[1])
                        elif len(chunks)>1:
                            z=chunks.pop()
                            chunks[-1]='\j'+z+chunks[-1]
                        else:
                            chunks.append('\j')
                        if yob[0]!='':
                            if len(yob[0])<(width-cur_len):
                                chunks.append((width-cur_len-len(yob[0]))*' ')
                            else:
                                chunks.append((width-len(yob[0]))*' ')
                            chunks.append(yob[0])
                        else:
                            chunks.append((width-cur_len)*' ')
                elif '\\n' in chunks[-1] and not '\\\\n' in chunks[-1]:
                        yob=chunks[-1].split('\\n')
                        chunks.pop()
                        if yob[1]!='':
                            chunks.append(yob[1])
                        elif len(chunks)>1:
                            z=chunks.pop()
                            chunks[-1]='\j'+z+chunks[-1]
                        else:
                            chunks.append('\j')
                        chunks.append(' '*50)
                        if yob[0]!='':
                            if len(yob[0])<(width-cur_len):
                                chunks.append((width-cur_len-len(yob[0]))*' ')
                            else:
                                chunks.append((width-len(yob[0]))*' ')
                            chunks.append(yob[0])
                        else:
                            chunks.append((width-cur_len)*' ')       
                elif '\g' in chunks[-1] and not '\\\g' in chunks[-1]:
                        yob=chunks[-1].split('\g')
                        chunks.pop()
                        if yob[1]!='':
                            chunks.append('\j         '+yob[1])
                        elif len(chunks)>1:
                            z=chunks.pop()
                            chunks[-1]='\j         '+z+chunks[-1]
                        if yob[0]!='':
                            if len(yob[0])<(width-cur_len):
                                chunks.append((width-cur_len-len(yob[0]))*' ')
                            else:
                                chunks.append((width-len(yob[0]))*' ')
                            chunks.append(yob[0])
                        else:
                            chunks.append((width-cur_len)*' ')
                            
                l = len(chunks[-1])-2*(chunks[-1].startswith('\j') and cur_len==0)
                if cur_len + l <= width:
                    cur_line.append(chunks.pop())
                    cur_len += l
                else:
                    break
            if chunks and len(chunks[-1]) > width:
                self._handle_long_word(chunks, cur_line, cur_len, width)
                cur_len = sum(map(len, cur_line))
            if self.drop_whitespace and cur_line and cur_line[-1].strip() == '':
                cur_len -= len(cur_line[-1])
                del cur_line[-1]

            if cur_line:
                if (self.max_lines is None or
                    len(lines) + 1 < self.max_lines or
                    (not chunks or
                     self.drop_whitespace and
                     len(chunks) == 1 and
                     not chunks[0].strip()) and cur_len <= width):
                    lines.append(indent + ''.join(cur_line))
                else:
                    while cur_line:
                        if (cur_line[-1].strip() and
                            cur_len + len(self.placeholder) <= width):
                            cur_line.append(self.placeholder)
                            lines.append(indent + ''.join(cur_line))
                            break
                        cur_len -= len(cur_line[-1])
                        del cur_line[-1]
                    else:
                        if lines:
                            prev_line = lines[-1].rstrip()
                            if (len(prev_line) + len(self.placeholder) <=
                                    self.width):
                                lines[-1] = prev_line + self.placeholder
                                break
                        lines.append(indent + self.placeholder.lstrip())
                    break

        return lines

    def _split_chunks(self, text):
        text = self._munge_whitespace(text)
        return self._split(text)

    # -- Public interface ----------------------------------------------

    def wrap(self, text):
        chunks = self._split_chunks(text)
        if self.fix_sentence_endings:
            self._fix_sentence_endings(chunks)
        return self._wrap_chunks(chunks)

    def fill(self, text):
        return "\n".join(self.wrap(text))
    
# -- Convenience interface ---------------------------------------------

def wrap(text, width=70, **kwargs):
    w = TextWrapper(width=width, **kwargs)
    return w.wrap(text)

def fill(text, width=70, **kwargs):
    w = TextWrapper(width=width, **kwargs)
    return w.fill(text)

def shorten(text, width, **kwargs):
    w = TextWrapper(width=width, max_lines=1, **kwargs)
    return w.fill(' '.join(text.strip().split()))


# -- Loosely related functionality -------------------------------------

_whitespace_only_re = re.compile('^[ \t]+$', re.MULTILINE)
_leading_whitespace_re = re.compile('(^[ \t]*)(?:[^ \t\n])', re.MULTILINE)

def dedent(text):
    margin = None
    text = _whitespace_only_re.sub('', text)
    indents = _leading_whitespace_re.findall(text)
    for indent in indents:
        if margin is None:
            margin = indent
        elif indent.startswith(margin):
            pass
        elif margin.startswith(indent):
            margin = indent
        else:
            for i, (x, y) in enumerate(zip(margin, indent)):
                if x != y:
                    margin = margin[:i]
                    break
    if 0 and margin:
        for line in text.split("\n"):
            assert not line or line.startswith(margin), \
                   "line = %r, margin = %r" % (line, margin)

    if margin:
        text = re.sub(r'(?m)^' + margin, '', text)
    return text


def indent(text, prefix, predicate=None):
    if predicate is None:
        def predicate(line):
            return line.strip()

    def prefixed_lines():
        for line in text.splitlines(True):
            yield (prefix + line if predicate(line) else line)
    return ''.join(prefixed_lines())


HEADER_LENGTH = 10
PORT = 1234
hostname = socket.gethostname()
SERVER = socket.gethostbyname(hostname)
ADDRESS = (SERVER, PORT) 
FORMAT = "utf-8"
COR_1='#000000'

# Create a new client socket 
# and connect to the server 
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
client.connect(ADDRESS)

class bloco:
    def __init__(self,premod,posmod,sn):
        self.premod=premod
        self.posmod=posmod
        self.sn=sn

class msg:
    def __init__(self,destiny,content):
        self.destiny=destiny
        self.content=content

class roll:
    def __init__(self,caller,receiver,who):
        self.caller=caller
        self.receiver=receiver
        self.who=who

# GUI class for the chat 
class GUI: 
        # constructor method 
        def __init__(self): 
                
                # chat window which is currently hidden 
                self.Window = Tk() 
                self.Window.withdraw() 
                
                # login window 
                self.login = Toplevel() 
                # set the title 
                self.login.title("Login") 
                self.login.resizable(width = False, 
                                                        height = False) 
                self.login.configure(width = 700, 
                                                        height = 300) 
                # create a Label 
                self.pls = Label(self.login, 
                                        text = "Please login to continue", 
                                        justify = CENTER,
                                        font = "Courier 14 bold") 
                
                self.pls.place(relheight = 0.15, 
                                        relx = 0.5, 
                                        rely = 0.09,
                                        anchor=CENTER)
                
                # create a Label 
                self.labelName = Label(self.login, 
                                                        text = "Username: ",
                                                        font = "Courier 14") 
                
                self.labelName.place(relheight = 0.2, 
                                                        relx = 0.25, 
                                                        rely = 0.16) 
                
                # create a entry box for 
                # typing the message 
                self.entryName = Entry(self.login, 
                                                        font = "Courier 14") 
                
                self.entryName.place(relwidth = 0.3, 
                                                        relheight = 0.12, 
                                                        relx = 0.45, 
                                                        rely = 0.2) 
                
                # set the focus of the curser 
                self.entryName.focus() 
                
                # create a Continue Button 
                # along with action 
                self.go = Button(self.login, 
                                                text = "CONTINUE", 
                                                font = "Courier 14 bold", 
                                                command = lambda: self.goAhead(self.entryName.get())) 

                self.entryName.bind('<Return>',(lambda event: self.goAhead(self.entryName.get())))
                self.login.protocol("WM_DELETE_WINDOW", self.on_closing)  
                self.go.place(relx = 0.4, 
                                        rely = 0.55) 
                self.Window.mainloop() 

        def on_closing(self):
                client.close()
                sys.exit()
                
        def goAhead(self, name):
                my_username = name.encode(FORMAT)
                my_username_header = f"{len(my_username):<{HEADER_LENGTH}}".encode(FORMAT)
                client.send(my_username_header + my_username)
                server_message_header=client.recv(HEADER_LENGTH)
                server_message_length = int(server_message_header.decode(FORMAT).strip())
                server_message=client.recv(server_message_length).decode(FORMAT)
                if server_message=='Ok':
                        global namer
                        namer=name
                        try:
                            color=askcolor(title ="Escolha a cor do seu usuário")[1].encode(FORMAT)
                        except:
                            client.close()
                            sys.exit()
                        colour=color
                        color_header=f"{len(color):<{HEADER_LENGTH}}".encode(FORMAT)
                        client.send(color_header + color)
                        self.login.destroy()
                        self.layout(name)
                        # the thread to receive messages 
                        rcv = threading.Thread(target=self.receive) 
                        rcv.start()
                        clr = threading.Thread(target=self.colorloop)
                        clr.start()
                else:
                        self.pls.config(text=server_message)

        # The main layout of the chat 
        def layout(self,name): 
                
                self.name = name 
                # to show chat window 
                self.Window.deiconify() 
                self.Window.title("CHATROOM") 
                self.Window.resizable(width = False, 
                                                        height = False) 
                self.Window.configure(width = 570, 
                                                        height = 550, 
                                                        bg = COR_1)

                self.labelHead = Label(self.Window, 
                                                        bg = COR_1,
                                                        text = self.name , 
                                                        font = "Courier 14 bold", 
                                                        pady = 5) 

                self.labelHead.place(relwidth = 1) 
                self.line = Label(self.Window, 
                                                width = 450) 
                
                self.line.place(relwidth = 1, 
                                                rely = 0.07, 
                                                relheight = 0.012) 
                
                self.textCons = Text(self.Window, 
                                                        width = 20, 
                                                        height = 2, 
                                                        bg = COR_1,  
                                                        font = "Courier 14", 
                                                        padx = 5, 
                                                        pady = 5) 
                
                self.textCons.place(relheight = 0.745, 
                                                        relwidth = 1, 
                                                        rely = 0.08) 
                
                self.Window.bind_all("<MouseWheel>", self.on_mousewheel)

                self.labelBottom = Label(self.Window, 
                                                                bg = COR_1, 
                                                                height = 80) 
                
                self.labelBottom.place(relwidth = 1, 
                                                        rely = 0.825) 
                
                self.entryMsg = Entry(self.labelBottom, 
                                                        bg = COR_1, 
                                                        font = "Courier 12") 
                
                # place the given widget 
                # into the gui window 
                self.entryMsg.place(relwidth = 0.74, 
                                                        relheight = 0.06, 
                                                        rely = 0.008, 
                                                        relx = 0.011) 
                
                self.entryMsg.focus() 
                
                # create a Send Button 
                self.buttonMsg = Button(self.labelBottom, 
                                                                text = "Send", 
                                                                font = "Courier 12 bold", 
                                                                width = 20, 
                                                                bg = COR_1,
                                                                command = lambda : self.sendButton(self.entryMsg.get())) 
                
                self.Window.bind('<Return>',(lambda event: self.sendButton(self.entryMsg.get())))

                self.Window.bind("<Up>",self.up_down)

                self.Window.bind("<Down>",self.up_down)

                self.buttonMsg.place(relx = 0.77, 
                                                        rely = 0.008, 
                                                        relheight = 0.06, 
                                                        relwidth = 0.22) 
                
                self.textCons.config(cursor = "arrow") 
                
                self.textCons.config(state = DISABLED) 

                self.line2 = Label(self.Window, 
                                                width = 450)

                self.line2.place(relwidth = 1, 
                                                rely = 0.825, 
                                                relheight = 0.012)

                self.Window.protocol("WM_DELETE_WINDOW", self.on_closing)
        def on_mousewheel(self, event):
            self.textCons.yview_scroll(-1*int(event.delta/120), "units")

        def up_down(self,event):
                if event.keysym == 'Up':
                        self.textCons.yview_scroll(-1,'units')
                if event.keysym == 'Down':
                        self.textCons.yview_scroll(1,'units')

        def colorloop(self):
            global colors
            try:
                while True:
                    for i in range(len(colors)):
                        time.sleep(0.5)
                        self.changecolor(i)
            except:
                client.close()
                sys.exit()

        def changecolor(self,i):
            global colors
            self.buttonMsg.config(fg=colors[(i-9)%100])
            self.entryMsg.config(fg=colors[(i-9)%100])
            self.labelHead.config(fg=colors[i])
            self.line.config(bg=colors[(i-2)%100])
            self.line2.config(bg=colors[(i-7)%100])
        
        # function to basically start the thread for sending messages 
        def sendButton(self, msg):
                self.textCons.config(state = DISABLED) 
                self.msg=msg 
                self.entryMsg.delete(0, END) 
                snd= threading.Thread(target = self.sendMessage) 
                snd.start() 

        # function to receive messages 
        def receive(self): 
                while True: 
                        try:
                                message_header = client.recv(HEADER_LENGTH)
                                message_length = int(message_header.decode(FORMAT).strip())
                                message = client.recv(message_length)
                                message=pickle.loads(message)
                                message_final = message.sender+' > '+message.content
                                # insert messages to text box 
                                self.textCons.config(state = NORMAL)
                                self.textCons.tag_configure(message.cor,foreground=message.cor)
                                textlis=wrap(message_final,width=50)
                                for u in range(len(textlis)):
                                    if textlis[u].startswith('\j'):
                                        textlis[u]=textlis[u].replace('\j','',1)
                                        textlis[u]=textlis[u].rstrip()
                                    else:
                                        textlis[u]=textlis[u].strip()
                                textlis.append('')
                                for u in range(len(textlis)-1):
                                    if textlis[u]=='':
                                        self.textCons.insert(END,'\n')
                                    elif textlis[u+1]!='' and not textlis[u+1].startswith(' '):
                                        linha=justify(textlis[u],50)
                                        self.textCons.insert(END, linha+'\n',message.cor)
                                    else:
                                        self.textCons.insert(END, textlis[u]+'\n',message.cor)
                                self.textCons.insert(END,'\n')
                                self.textCons.see(END)
                                self.textCons.config(state = DISABLED) 
                        except: 
                                # an error will be printed on the command line or console if there's an error 
                                client.close()
                                sys.exit()
                
        # function to send messages 
        def sendMessage(self):
                self.textCons.config(state=DISABLED)
                while True:
                        message_sent = pickle.dumps(msg(namer,self.msg))
                        message_sent_header = f"{len(message_sent):<{HEADER_LENGTH}}".encode(FORMAT)
                        client.send(message_sent_header+message_sent)    
                        break   

# create a GUI class object
g = GUI()

