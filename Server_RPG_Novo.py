import socket
import select
import pickle
import random
import re
from decimal import *
getcontext()
getcontext().prec=20

HEADER_LENGTH = 10

hostname = socket.gethostname()

IP = socket.gethostbyname(hostname)
PORT = 1234
class res:
    def __init__(self,p,crit,r,advan):
        self.p=p
        self.r=r
        self.crit=crit
        self.advan=advan

class msg:
    def __init__(self,sender,content,cor):
        self.sender=sender
        self.content=content
        self.cor=cor

class roll:
    2

# Create a socket
# socket.AF_INET - address family, IPv4, some other possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
# socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# SO_ - socket option
# SOL_ - socket option level
# Sets REUSEADDR (as a socket option) to 1 on socket
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind, so server informs operating system that it's going to use given IP and port
# For a server using 0.0.0.0 means to listen on all available interfaces, useful to connect locally to 127.0.0.1 and remotely to LAN interface IP
server_socket.bind((IP, PORT))

# This makes server listen to new connections
server_socket.listen()

# List of sockets for select.select()
sockets_list = [server_socket]

# List of connected clients - socket as a key, user header and name as data
clients = {}

espera_de_cor={}

rolls={}
        
print(f'Listening for connections on {IP}:{PORT}...')

colore='#ffffff'
instructions='\kComandos:\n*Rolar dados.\\nExemplo: "-dice -3+5d6-3-7d8+2"\n*Iniciativa. Retorna uma sequência randomizada e uniformemente espaçada de Ups e Downs: Caso o número de integrantes de cada grupo seja igual, antes determinem quem será Up e quem será Down.\\nExemplo: "-init 5x4" (Combate de 4 contra 5)\\n***OBS. Os comandos devem começar imediatamente com a chave, porém subsequentes usos de espaço são irrelevantes, a não ser em mensagens privadas, onde são mantidos***' 
instructions=pickle.dumps(msg('Server',instructions,colore))

def send_new_message(notifi,client_socket):
    notifi_header = f"{len(notifi):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket.send(notifi_header+notifi)

def send_rolagem(rolagem,r,crit):
    if rolagem['send_type']=='hidden':
        notifi="Rolagem entre "+clients[rolagem['receiver']]['data']+' e '+str(clients[rolagem['caller']]['data'])+'\gNet Advantage: '+str(rolagem['advan'])
        notifi2=pickle.dumps(msg('Server',notifi,colore))
        send_new_message(notifi2,rolagem['caller'])
        opposite_message=(rolagem['hidden_message']=='n')*'Sim.'+(rolagem['hidden_message']=='s')*'Não.'
        rolagem['hidden_message']=(rolagem['hidden_message']=='s')*'Sim.'+(rolagem['hidden_message']=='n')*'Não.'
        notifi+='\g'+(r<=rolagem['p'])*rolagem['hidden_message']+(r>rolagem['p'])*opposite_message
        notifi=pickle.dumps(msg('Server',notifi,colore))
        send_new_message(notifi,rolagem['receiver'])
        print((r<=rolagem['p'])*rolagem['hidden_message']+(r>rolagem['p'])*opposite_message)
    else:
        notifi="Rolagem entre "+clients[rolagem['receiver']]['data']+' e '+str(clients[rolagem['caller']]['data'])
        if r<=crit:
            notifi+='\gCrítico'
        elif r<=rolagem['p']:
            notifi+='\gSucesso'
        else:
            notifi+='\gFracasso'
        rolagem['p'],crit,r=2000-rolagem['p'],2000-crit,2000-r
        notifi+='\gNet Advantage: '+str(rolagem['advan'])+'\gInfo: '+str(r)+' de '+str(rolagem['p'])
        print(notifi)
        notifi=pickle.dumps(msg('Server',notifi,colore))
        notifi2=pickle.dumps(res(rolagem['p'],crit,r,rolagem['advan']))
        if rolagem['send_type']=='me':
            send_new_message(notifi,rolagem['caller'])
            send_new_message(notifi2,rolagem['caller'])
        elif rolagem['send_type']=='you':
            send_new_message(notifi,rolagem['receiver'])
            send_new_message(notifi2,rolagem['receiver'])
        elif rolagem['send_type']=='we':
            send_new_message(notifi,rolagem['caller'])
            send_new_message(notifi2,rolagem['caller'])
            send_new_message(notifi,rolagem['receiver'])
            send_new_message(notifi2,rolagem['receiver'])        

def apply_posmod_pre(receiver,fonte,rolagem):
    for mod in fonte['posmod']:
        if mod[0]!=0:
            for i in mod[1]:
                if type(i)==tuple:
                    if i[0]!='*':
                        if i[1]!=0:
                            rolagem['p']+=i[0]*(i[1]+1)*25
                            if random.randint(1,40)<=i[0]*i[1]:
                                mod[0]-=1
                                notifi='Usado o recurso '+str(i[0])+'d'+str(i[1])+' em '+str(mod[1])+' na rolagem entre '+clients[rolagem['caller']]['data']+' e '+clients[rolagem['receiver']]['data']+'. Restam '+str(mod[0])+' desse recurso.'
                                notifi=pickle.dumps(msg('Server',notifi,colore))
                                send_new_message(notifi,receiver)
                        else:
                            rolagem['p']+=i[0]*50
                            if random.randint(1,40)<=i[0]:
                                mod[0]-=1
                                notifi='Usado o recurso '+str(i[0])+' em '+str(mod[1])+' na rolagem entre '+clients[rolagem['caller']]['data']+' e '+clients[rolagem['receiver']]['data']+'. Restam '+str(mod[0])+' desse recurso.'
                                notifi=pickle.dumps(msg('Server',notifi,colore))
                                send_new_message(notifi,receiver)

                    else:
                        um=(rolagem['advan']==1)*3+(rolagem['advan']==2)*5+(rolagem['advan']>2)*6-(rolagem['advan']==-1)*3-(rolagem['advan']==-2)*5-(rolagem['advan']<-2)*6
                        rolagem['advan']+=i[1]
                        dois=(rolagem['advan']==1)*3+(rolagem['advan']==2)*5+(rolagem['advan']>2)*6-(rolagem['advan']==-1)*3-(rolagem['advan']==-2)*5-(rolagem['advan']<-2)*6
                        if random.randint(1,20)<=abs(um-dois):
                            mod[0]-=1
                            notifi='Usado o recurso '+str(i[1])+'*Advantage em '+str(mod[1])+' na rolagem entre '+clients[rolagem['caller']]['data']+' e '+clients[rolagem['receiver']]['data']+'. Restam '+str(mod[0])+' desse recurso.'
                            notifi=pickle.dumps(msg('Server',notifi,colore))
                            send_new_message(notifi,receiver)

def apply_posmod_pos(receiver,fonte,rolagem,r):
    for mod in fonte['posmod']:
        if mod[0]!=0:
            for i in mod[1]:
                if type(i)==int:
                    if r<=rolagem['p'] and i<0:
                        if r-i*50>rolagem['p']:
                            mod[0]-=1
                            notifi='Usado o recurso '+i+' em '+mod[1]+' na rolagem entre '+clients[rolagem['caller']]['data']+' e '+clients[rolagem['receiver']]['data']+'. Restam '+str(mod[0])+' desse recurso.'
                            notifi=pickle.dumps(msg('Server',notifi,colore))
                            send_new_message(notifi,receiver)
                            rolagem['p']+=i*50
                    elif r>rolagem['p'] and i>0:
                        if r-i*50<=rolagem['p']:
                            mod[0]-=1
                            notifi='Usado o recurso '+i+' em '+mod[1]+' na rolagem entre '+clients[rolagem['caller']]['data']+' e '+clients[rolagem['receiver']]['data']+'. Restam '+str(mod[0])+' desse recurso.'
                            notifi=pickle.dumps(msg('Server',notifi,colore))
                            send_new_message(notifi,receiver)
                            rolagem['p']+=i*50
                elif type(i)==list:
                    if r<=rolagem['p'] and i[0]<0:
                        if r-i[0]*i[1]*50>rolagem['p']:
                            mod[0]-=1
                            notifi='Usado o recurso '+i+' em '+mod[1]+' na rolagem entre '+clients[rolagem['caller']]['data']+' e '+clients[rolagem['receiver']]['data']+'. Restam '+str(mod[0])+' desse recurso.'
                            notifi=pickle.dumps(msg('Server',notifi,colore))
                            send_new_message(notifi,receiver)
                            rolagem['p']+=i[0]*random.randint(1,i[1])*50+1
                    elif r>rolagem['p'] and i[0]>0:
                        if r-i[0]*i[1]*50<=rolagem['p']:
                            mod[0]-=1
                            notifi='Usado o recurso '+i+' em '+mod[1]+' na rolagem entre '+clients[rolagem['caller']]['data']+' e '+clients[rolagem['receiver']]['data']+'. Restam '+str(mod[0])+' desse recurso.'
                            notifi=pickle.dumps(msg('Server',notifi,colore))
                            send_new_message(notifi,receiver)
                            rolagem['p']+=i[0]*random.randint(1,i[1])*50+1
                elif i[0]=='%':
                    um=(rolagem['advan']==1)*300+(rolagem['advan']==2)*500+(rolagem['advan']>2)*600-(rolagem['advan']==-1)*300-(rolagem['advan']==-2)*500-(rolagem['advan']<-2)*600
                    rolagem['advan']+=i[1]
                    dois=(rolagem['advan']==1)*300+(rolagem['advan']==2)*500+(rolagem['advan']>2)*600-(rolagem['advan']==-1)*300-(rolagem['advan']==-2)*500-(rolagem['advan']<-2)*600
                    if r<=rolagem['p'] and i[1]<0:
                        if r+um-dois>rolagem['p']:
                            rolagem['p']+=-um+dois
                            mod[0]-=1
                            notifi='Usado o recurso '+str(i[1])+'*Advantage em '+str(mod[1])+' na rolagem entre '+clients[rolagem['caller']]['data']+' e '+clients[rolagem['receiver']]['data']+'. Restam '+str(mod[0])+' desse recurso.'
                            notifi=pickle.dumps(msg('Server',notifi,colore))
                            send_new_message(notifi,receiver)
                    elif r>rolagem['p'] and i[1]>0:
                        if r+um-dois<rolagem['p']:
                            rolagem['p']+=-um+dois
                            mod[0]-=1
                            notifi='Usado o recurso '+str(i[1])+'*Advantage em '+str(mod[1])+' na rolagem entre '+clients[rolagem['caller']]['data']+' e '+clients[rolagem['receiver']]['data']+'. Restam '+str(mod[0])+' desse recurso.'
                            notifi=pickle.dumps(msg('Server',notifi,colore))
                            send_new_message(notifi,receiver)
                    else:
                        rolagem['advan']-=i[1]

def rola(rolagem):
    global rolls
    if rolagem['ready']!=2:
        return
    caller=rolagem['caller']
    recibru=rolagem['receiver']
    rolls[recibru].pop()
    apply_posmod_pre(recibru,rolagem,rolagem)
    apply_posmod_pre(caller,rolls[caller],rolagem)
    rolagem['p']+=(rolagem['advan']==1)*300+(rolagem['advan']==2)*500+(rolagem['advan']>2)*600
    rolagem['p']+=-(rolagem['advan']==-1)*300-(rolagem['advan']==-2)*500-(rolagem['advan']<-2)*600
    r=random.randint(0,1999)
    while True:
        confere=rolagem['p']
        apply_posmod_pos(recibru,rolagem,rolagem,r)
        apply_posmod_pos(caller,rolls[caller],rolagem,r)
        if confere==rolagem['p']:
            break
    crit=rolagem['p']/10+(rolagem['p']>rolagem['q'])*(rolagem['p']-rolagem['q'])
    send_rolagem(rolagem,r,crit)
            
# Handles message receiving
def receive_message(client_socket):

    try:

        # Receive our "header" containing message length, it's size is defined and constant
        message_header = client_socket.recv(HEADER_LENGTH)

        # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
        if not len(message_header):
            return False

        # Convert header to int value
        message_length = int(message_header.decode('utf-8').strip())

        # Return an object of message header and message data
        return {'header': message_header, 'data': client_socket.recv(message_length)}

    except:

        # If we are here, client closed connection violently, for example by pressing ctrl+c on his script
        # or just lost his connection
        # socket.close() also invokes socket.shutdown(socket.SHUT_RDWR) what sends information about closing the socket (shutdown read/write)
        # and that's also a cause when we receive an empty message
        return False

while True:

    # Calls Unix select() system call or Windows select() WinSock call with three parameters:
    #   - rlist - sockets to be monitored for incoming data
    #   - wlist - sockets for data to be send to (checks if for example buffers are not full and socket is ready to send some data)
    #   - xlist - sockets to be monitored for exceptions (we want to monitor all sockets for errors, so we can use rlist)
    # Returns lists:
    #   - reading - sockets we received some data on (that way we don't have to check sockets manually)
    #   - writing - sockets ready for data to be send thru them
    #   - errors  - sockets with some exceptions
    # This is a blocking call, code execution will "wait" here and "get" notified in case any action should be taken
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)


    # Iterate over notified sockets
    for notified_socket in read_sockets:

        # If notified socket is a server socket - new connection, accept it
        if notified_socket == server_socket:

            # Accept new connection
            # That gives us new socket - client socket, connected to this given client only, it's unique for that client
            # The other returned object is ip/port set
            
            client_socket, client_address = server_socket.accept()
            sockets_list.append(client_socket)

        # Else existing socket is sending a message
        else:
            if notified_socket in clients:
                # Receive message
                message = receive_message(notified_socket)

                # If False, client disconnected, cleanup
                if message is False:
                        
                    print('Closed connection from: {}.'.format(clients[notified_socket]['data']))
                    for client_socket in clients[notified_socket]['calling']:
                        notifi=clients[notified_socket]['data']+" desconectou enquanto chamava você. Você não está mais rolando."
                        notifi=pickle.dumps(msg('Server',notifi,colore))
                        send_new_message(notifi,client_socket)
                        clients[client_socket]['rolling']=0
                    try:
                        clients[rolls[notified_socket][0]['caller']]['calling'].remove(notified_socket)
                        if clients[rolls[notified_socket][0]['caller']]['calling']==[]:
                            notifi=clients[notified_socket]['data']+" desconectou e era sua única chamada. Você não está mais rolando."
                            notifi=pickle.dumps(msg('Server',notifi,colore))
                            send_new_message(notifi,rolls[notified_socket][0]['caller'])
                            clients[rolls[notified_socket][0]['caller']]['rolling']=0
                        else:
                            notifi=clients[notified_socket]['data']+" desconectou porém você ainda tem chamadas. Você continua rolando."
                            notifi=pickle.dumps(msg('Server',notifi,colore))
                            send_new_message(notifi,rolls[notified_socket][0]['caller'])
                    except:
                        pass
                    
                    # Remove from list for socket.socket()
                    sockets_list.remove(notified_socket)

                    newuser=pickle.dumps({'name': clients[notified_socket]['data']})
                    newuser_header=f"{len(newuser):<{HEADER_LENGTH}}".encode('utf-8')
                    
                    # Remove from our list of users
                    del clients[notified_socket]

                    for client_socket in clients:
                        client_socket.send(newuser_header+newuser)

                    continue

                # Get user by notified socket, so we will know who sent the message
                user = clients[notified_socket]
                messagepf=pickle.loads(message["data"])
                
                if type(messagepf).__name__=='msg':
                    messagepf.cor=user['cor']
                    if not messagepf.destiny:
                        messagepf.sender=user['data']
                        message['data']=pickle.dumps(messagepf)
                        message["header"]=f"{len(message['data']):<{HEADER_LENGTH}}".encode('utf-8')
                        for client_socket in clients:
                            client_socket.send(message["header"] + message['data'])
                    else:
                        messagepf.sender='Privado > '+user['data']
                        message['data']=pickle.dumps(messagepf)
                        message["header"]=f"{len(message['data']):<{HEADER_LENGTH}}".encode('utf-8')
                        for client_socket in clients:
                            if clients[client_socket]['data'] in messagepf.destiny:
                                client_socket.send(message["header"] + message['data'])
                        notified_socket.send(message["header"] + message['data'])

                elif type(messagepf).__name__=='roll':                       
                        if messagepf.who=='hidden':
                            notifi=pickle.dumps(msg('Server',"Confira o que você espera enviar ao oponente em caso de sucesso dele (s ou n).",colore))
                            send_new_message(notifi,notified_socket)
                        for client_socket in clients:
                            check=clients[client_socket]['data']
                            roladas=messagepf.receiver.count(check)
                            if roladas:
                                if not clients[client_socket]['rolling']:
                                    clients[client_socket]['rolling']+=roladas
                                    user['calling'].append(client_socket)
                                    notifi=pickle.dumps(msg('Server',check+" encontra-se disponível.",colore))
                                    send_new_message(notifi,notified_socket)
                                    notifi=user['data']+" iniciou "+str(roladas)+" rolagem(ns) com você com a tag "+messagepf.who+(roladas>1)*"\gRecomenda-se ler o resultado anterior para inserir o próximo bloco para evitar repetição de recursos."+"\gBloco da primeira rolagem:"
                                    notifi=pickle.dumps(msg('Server',notifi,colore))
                                    send_new_message(notifi,client_socket)
                                    send_new_message(message['data'],client_socket)
                                    rolls[client_socket]=[{'advan': 0,'receiver': client_socket,'caller': notified_socket,'ready':0,'p':1000,'q':2000,'send_type': messagepf.who}]
                                    for i in range(roladas-1):
                                        rolls[client_socket].append({'advan': 0,'receiver': client_socket,'caller': notified_socket,'ready':0,'p':1000,'q':2000,'send_type': messagepf.who})
                                else:
                                    notifi=check+" encontra-se indisponível."
                                    notifi=pickle.dumps(msg('Server',notifi,colore))
                                    send_new_message(notifi,notified_socket)
                        if user['calling']:
                            user['rolling']=1
                            notifi="Bloco comunitário:"
                            notifi=pickle.dumps(msg('Server',notifi,colore))
                            send_new_message(notifi,notified_socket)
                            rolls[notified_socket]={'send_type':messagepf.who}
                        else:
                            notifi="Ninguém aceitou."
                            notifi=pickle.dumps(msg('Server',notifi,colore))
                            send_new_message(notifi,notified_socket)

                elif type(messagepf).__name__=='bloco':
                    if user['rolling']:
                        rolls[notified_socket][0]['posmod']=messagepf.posmod
                        if not user['calling']:
                            rolls[notified_socket][-1]['p']+=50*messagepf.premod[0]
                            rolls[notified_socket][-1]['advan']+=messagepf.premod[1]
                            rolls[notified_socket][-1]['ready']+=1
                            rola(rolls[called_socket][-1]) 
                        else:
                            if rolls[notified_socket]['send_type']=='hidden':
                                for called_socket in user['calling']:
                                    for i in range(len(rolls[called_socket])):
                                        rolls[called_socket][i]['hidden_message']=messagepf.sn
                            for called_socket in user['calling']:
                                for i in range(len(rolls[called_socket])):
                                    rolls[called_socket][i]['p']+=50*messagepf.premod[0]
                                    rolls[called_socket][i]['advan']+=messagepf.premod[1]
                                    rolls[called_socket][i]['ready']+=1
                                    rola(rolls[called_socket][i]) 
                        user['rolling']-=1
                        user['calling']=[]
                        notifi='Premod: '+str(messagepf.premod)+'\nPosmod: '+messagepf.posmod+"\gFinalizado! Mais "+str(user['rolling'])+' rolagens.'
                        notifi=pickle.dumps(msg('Server',notifi,colore))
                        send_new_message(notifi,notified_socket)
                    else:
                        notifi="Você não se encontra rolando no momento."
                        notifi=pickle.dumps(msg('Server',notifi,colore))
                        send_new_message(notifi,notified_socket)
                            
            elif notified_socket in espera_de_cor:
                cor=receive_message(notified_socket)
                if cor is False:
                        sockets_list.remove(notified_socket)
                else:
                    cordec=cor['data'].decode('utf-8')
                    newuser=pickle.dumps({'name': espera_de_cor[notified_socket]['data'], 'color': cordec})
                    newuser_header=f"{len(newuser):<{HEADER_LENGTH}}".encode('utf-8')
                    alreadyuser=[]
                    for client_socket in clients:
                        alreadyuser.append({'name': clients[client_socket]['data'], 'color': clients[client_socket]['cor']})
                        client_socket.send(newuser_header+newuser)
                    # print(alreadyuser)
                    alreadyuser=pickle.dumps(alreadyuser)
                    auser_header=f"{len(alreadyuser):<{HEADER_LENGTH}}".encode('utf-8')
                    notified_socket.send(auser_header+alreadyuser)
                    # Save username and username header                        
                    clients[notified_socket] = espera_de_cor[notified_socket]
                    clients[notified_socket]['calling'] = []
                    clients[notified_socket]['rolling'] = 0
                    clients[notified_socket]['cor']=cordec
                    print('Accepted new connection from user: {}.'.format(clients[notified_socket]['data']))
                    send_new_message(instructions,notified_socket)
                del espera_de_cor[notified_socket]
            else:
                    # Client should send his name right away, receive it
                    user = receive_message(notified_socket)

                    # If False - client disconnected before he sent his name
                    if user is False:
                            
                            sockets_list.remove(notified_socket)

                    else:
                        
                        login_message='ok'
                        user['data']=user['data'].decode('utf-8').replace(' ','_')

                        if len(sockets_list)>=10:
                            sockets_list.remove(notified_socket)
                            login_message='Servidor lotado'

                        if login_message=='ok':
                            for socket in clients:
                                if clients[socket]['data']==user['data']:
                                    login_message='Username já em uso, tente outro'

                        if login_message=='ok':
                            if user['data']=='Server' or user['data']=='':
                                login_message='Username não pode ser Server ou ser em branco, tente outro'

                        if login_message=='ok':
                            if '\\' in user['data']:
                                login_message='Retire caracteres \ do username'

                        if login_message=='ok':
                            if len(user['data'])>12:
                                login_message='Username pode conter até 12 caracteres, tente outro'
                            else:
                                espera_de_cor[notified_socket]=user
            
                        login_message=login_message.encode('utf-8')
                        login_message_header=f"{len(login_message):<{HEADER_LENGTH}}".encode('utf-8')
                        notified_socket.send(login_message_header+login_message)

    # It's not really necessary to have this, but will handle some socket exceptions just in case
    for notified_socket in exception_sockets:

        # Remove from list for socket.socket()
        sockets_list.remove(notified_socket)

        # Remove from our list of users
        del clients[notified_socket]

            


