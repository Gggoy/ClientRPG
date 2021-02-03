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

class res:
    def __init__(self,p,crit,r):
        self.p=p
        self.r=r
        self.crit=crit

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

        def onPlayerClick(self, c):
            self.playerBtts[c].config(bg=self.playerBtts[c].cget('fg'), fg=self.playerBtts[c].cget('bg'))
            self.players[c]['selected'] = not self.players[c]['selected']

        def AllClick(self):
            if self.tempButton.cget('text')=='Select All':
                self.tempButton.config(text='Exclude All')
                for c in range(len(self.playerBtts)):
                    self.playerBtts[c].config(bg=self.players[c]['color'], fg='black')
                    self.players[c]['selected'] = True
            else:
                self.tempButton.config(text='Select All')
                for c in range(len(self.playerBtts)):
                    self.playerBtts[c].config(bg='black', fg=self.players[c]['color'])
                    self.players[c]['selected'] = False

        def createSidebarButtons(self):
            for playerBtt in self.playerBtts:
                playerBtt.destroy()

            self.playerBtts = []

            for i in range(len(self.players)):
                tempButton = Button(self.sidebar,
                                    fg = self.players[i]['color'],
                                    bg = 'black', text = self.players[i]['name'],
                                    font = "Courier 14 bold",
                                    command=lambda c=i: self.onPlayerClick(c))
                self.playerBtts.append(tempButton)
                self.playerBtts[-1].place(relwidth=1, relheight=0.1, rely = 0.1*(len(self.playerBtts)-1))
            self.tempButton = Button(self.sidebar,
                                    fg = 'white',
                                    bg = 'black', text = 'Select All',
                                    font = "Courier 14 bold",
                                    command=lambda: self.AllClick())
            self.tempButton.place(relwidth=1, relheight=0.1, rely = 0.1*len(self.playerBtts))
                
        def displayres(self,res):
            self.label.config(text='Crítico: '+str(res.crit)+'; Sucesso: '+str(res.p)+'; Rolado: '+str(res.r))
            self.progress['value']=0
            res.p=(2000-res.p)//5
            res.r=(2000-res.r)//5
            res.crit=(2000-res.crit)//5
            self.barracrit1.place(x=res.crit+1)
            self.barrap1.place(x=res.p+1)
            self.barracrit2.place(x=res.crit+3)
            self.barrap2.place(x=res.p+3)
            for i in range(9):
                if 4*self.progress['value']+2**(8-i)<=res.r:
                    self.progress['value']+=2**(6-i)
                    if self.progress['value']==res.r:
                        break
                time.sleep(0.5)

        def on_closing(self):
                client.close()
                sys.exit()
        
        def blocswitch(self):
            if not self.Window2.winfo_viewable():
                self.Window2.deiconify()
                self.blocbtt.config(text='<')
            else:
                self.Window2.withdraw()
                self.blocbtt.config(text='>')
                
        def goAhead(self, name):
                my_username = name.encode(FORMAT)
                my_username_header = f"{len(my_username):<{HEADER_LENGTH}}".encode(FORMAT)
                client.send(my_username_header + my_username)
                server_message_header=client.recv(HEADER_LENGTH)
                server_message_length = int(server_message_header.decode(FORMAT).strip())
                server_message=client.recv(server_message_length).decode(FORMAT)
                if server_message=='Ok':
                        try:
                            color=askcolor(title ="Escolha a cor do seu usuário")[1].encode(FORMAT)
                        except:
                            self.on_closing()
                        color_header=f"{len(color):<{HEADER_LENGTH}}".encode(FORMAT)
                        client.send(color_header + color)
                        self.login.destroy()
                        self.receive()
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
                self.Window.resizable(width = False, height = False) 
                self.Window.configure(width = 800, height = 500, bg = 'black')

                self.Window2=Tk()
                self.Window2.title("ROLL") 
                self.Window2.resizable(width = False, height = False) 
                self.Window2.configure(width = 500, height = 500, bg = 'black')
                self.label = Label(self.Window2, bg = 'black', width=50, text = '', font = "Courier 14 bold", pady=5) 
                self.label.pack(expand=False)
                self.progress = ttk.Progressbar(self.Window2, orient=HORIZONTAL, length = 406, mode='determinate')
                self.progress.pack(expand=False, padx=10, pady=10)
                self.progress['value']=1/4
                self.barracrit1=Label(self.progress, bg = 'red')                 
                self.barracrit1.place(relwidth=0.0025,relheight=1,x=1)
                self.barracrit2=Label(self.progress, bg = 'red')                 
                self.barracrit2.place(relwidth=0.0025,relheight=1,x=3)
                self.barrap1=Label(self.progress, bg = 'orange')                 
                self.barrap1.place(relwidth=0.0025,relheight=1,x=1)
                self.barrap2=Label(self.progress, bg = 'orange')                 
                self.barrap2.place(relwidth=0.0025,relheight=1,x=3)
                self.Window2.withdraw()

                self.sidebar = Frame(self.Window, bg = 'black', width=200, height=500)
                self.sidebar.pack(expand = False, fill = 'both', side = 'left')

                self.playerBtts = []
                self.createSidebarButtons()
                
                self.sep = Label(self.Window, bg = 'white')
                self.sep.pack(expand = False, fill = 'both', side = 'left')

                self.mainFrame = Frame(self.Window, width=562, height=500)
                self.mainFrame.pack(expand=False, side='left')

                self.sep2 = Label(self.Window, bg = 'white')
                self.sep2.pack(expand = False, fill = 'both', side = 'left')

                self.bttframe = Frame(self.Window, width=30, height=500)
                self.bttframe.pack(expand=False, side='left')

                self.blocbtt= Button(self.bttframe, 
                                                        text = ">", 
                                                        font = "Courier 12 bold", 
                                                        fg = 'white',
                                                        bg='black',
                                                        command = lambda : self.blocswitch())
                self.blocbtt.place(relheight=1,relwidth=1)

                self.labelHead = Label(self.mainFrame, bg = 'black', text = self.name, font = "Courier 14 bold", pady=5) 
                self.labelHead.place(relwidth=1)

                self.line = Label(self.mainFrame)                 
                self.line.place(relwidth=1,relheight=0.012,y=36)
                
                self.textCons = Text(self.mainFrame, 
                                                        width = 20, 
                                                        height = 2, 
                                                        bg = 'black',  
                                                        font = "Courier 14", 
                                                        padx = 5, 
                                                        pady = 5) 
                self.textCons.place(y=42, relheight = 0.745, relwidth = 1)

                self.line2 = Label(self.mainFrame)                 
                self.line2.place(relwidth=1,relheight=0.012,y=415)
                
                self.labelBottom = Label(self.mainFrame, bg = 'black', height = 79)     
                self.labelBottom.place(relwidth=1,y=421) 
                
                self.entryMsg = Entry(self.labelBottom, bg = 'black', font = "Courier 12") 
                self.entryMsg.place(width = 417, 
                                                        height = 65, 
                                                        y = 5, 
                                                        x = 5) 
                self.entryMsg.focus() 
                
                self.buttonMsg = Button(self.labelBottom, 
                                                            text = "Send", 
                                                            font = "Courier 12 bold", 
                                                            width = 10, 
                                                            bg = 'black',
                                                            command = lambda : self.sendButton(self.entryMsg.get())) 
                self.buttonMsg.place(x = 428, 
                                                    y = 5, 
                                                    height = 33, 
                                                    width = 63) 
                
                self.rollBtt = Button(self.labelBottom, 
                                                        text = "Roll", 
                                                        font = "Courier 12 bold", 
                                                        width = 10, 
                                                        bg = 'black')
                                                        #command = lambda : self.sendButton(self.entryMsg.get())) 
                self.rollBtt.place(x = 491, 
                                                y = 38, 
                                                height = 33, 
                                                width = 63) 

                self.textCons.config(cursor = "arrow") 
                self.textCons.config(state = DISABLED) 

                self.Window.bind_all("<MouseWheel>", self.on_mousewheel)
                self.Window.bind('<Return>',(lambda event: self.sendButton(self.entryMsg.get())))
                self.Window.bind("<Up>",self.up_down)
                self.Window.bind("<Down>",self.up_down)
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
                self.on_closing()

        def changecolor(self,i):
            global colors
            self.buttonMsg.config(fg=colors[(i-8)%100])
            self.rollBtt.config(fg=colors[(i-10)%100])
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
                        #try:
                                message_header = client.recv(HEADER_LENGTH)
                                message_length = int(message_header.decode(FORMAT).strip())
                                message = client.recv(message_length)
                                message=pickle.loads(message)
                                #if type(message).__name__!='list':
                                    #message=res(1000,100,7)
                                if type(message).__name__=='msg':
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
                                elif type(message).__name__=='dict':
                                    playerFlag = True
                                    for i in range(len(self.players)):
                                        if self.players[i]['name'] == message['name']:
                                            self.players.pop(i)
                                            playerFlag = False
                                            break
                                    if playerFlag:
                                        message['selected'] = False
                                        self.players.append(message)
                                    self.createSidebarButtons()
                                elif type(message).__name__=='res':
                                    if not self.Window2.winfo_viewable():
                                        self.Window2.deiconify()
                                    self.displayres(message)
                                else:
                                    self.players = []
                                    for dics in message:
                                        dics['selected'] = False
                                        self.players.append(dics)
                                    break
                        #except:   
                            #self.on_closing()
                
        # function to send messages 
        def sendMessage(self):
                self.textCons.config(state=DISABLED)
                destinatários = []
                for player in self.players:
                    if player['selected']:
                        destinatários.append(player['name'])
                while True:
                        message_sent = pickle.dumps(msg(destinatários,self.msg))
                        message_sent_header = f"{len(message_sent):<{HEADER_LENGTH}}".encode(FORMAT)
                        client.send(message_sent_header+message_sent)    
                        break   

# create a GUI class object
g = GUI()

