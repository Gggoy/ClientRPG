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

class msg:
    def __init__(self,sender,content,cor):
        self.sender=sender
        self.content=content
        self.cor=cor

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

instructions='\kComandos:\n*Rolar dados.\\nExemplo: "-dice -3+5d6-3-7d8+2"\n*Iniciativa. Retorna uma sequência randomizada e uniformemente espaçada de Ups e Downs: Caso o número de integrantes de cada grupo seja igual, antes determinem quem será Up e quem será Down.\\nExemplo: "-init 5x4" (Combate de 4 contra 5)\\n***OBS. Os comandos devem começar imediatamente com a chave, porém subsequentes usos de espaço são irrelevantes, a não ser em mensagens privadas, onde são mantidos***' 

print(f'Listening for connections on {IP}:{PORT}...')

colore='#ffffff'

def send_new_message(notifi,client_socket):
    notifi=pickle.dumps(msg('Server',notifi,colore))
    notifi_header = f"{len(notifi):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket.send(notifi_header+notifi)

def send_rolagem(rolagem,r,crit):
    if r<=crit:
        notifi='Crítico\gNet Advantage: '+str(rolagem['advan'])
    elif r<=rolagem['p']:
        notifi='Sucesso\gNet Advantage: '+str(rolagem['advan'])
    else:
        notifi='Fracasso\gNet Advantage: '+str(rolagem['advan'])
    notifi+=rolagem['res']*('\gInfo: '+str(round(20-20*r/rolagem['q'],2))+' de '+str(round(20-20*rolagem['p']/rolagem['q'],2)))+"\gRolagem de "+clients[rolagem['receiver']]['data']
    print(notifi+' e '+clients[rolagem['caller']]['data'])
    if rolagem['send_type']=='-me':
        send_new_message(notifi,rolagem['caller'])
    elif rolagem['send_type']=='-you':
        send_new_message(notifi,rolagem['receiver'])
    elif rolagem['send_type']=='-we':
        send_new_message(notifi,rolagem['caller'])
        send_new_message(notifi,rolagem['receiver'])
    else:
        opposite_message=(rolagem['hidden_message']=='n')*'Sim.'+(rolagem['hidden_message']=='s')*'Não.'
        rolagem['hidden_message']=(rolagem['hidden_message']=='s')*'Sim.'+(rolagem['hidden_message']=='n')*'Não.'
        send_new_message((r<=rolagem['p'])*rolagem['hidden_message']+(r>rolagem['p'])*opposite_message+'\gNet Advantage: '+str(rolagem['advan']),rolagem['receiver'])
        print((r<=rolagem['p'])*rolagem['hidden_message']+(r>rolagem['p'])*opposite_message)

def apply_posmod_pre(receiver,fonte,rolagem):
    for mod in fonte['posmod']:
        if mod[0]!=0:
            if 'd' in mod[1]:
                if '/' in mod[1]:
                    modsepa=mod[1].split('/')
                    for alternativa in modsepa:
                        if 'd' in alternativa and mod[0]:
                            rolagem['p']+=Decimal(alternativa.split('d')[0])*(int(alternativa.split('d')[1])+1)*5
                            if random.randint(1,20)<=int(alternativa.split('d')[1]):
                                mod[0]-=1
                                send_new_message('Usado o recurso '+alternativa+' em '+mod[1]+' na rolagem entre '+clients[rolagem['caller']]['data']+' e '+clients[rolagem['receiver']]['data']+'.',receiver)
                else:
                    rolagem['p']+=Decimal(mod[1].split('d')[0])*(int(mod[1].split('d')[1])+1)*5
                    if random.randint(1,20)<=int(mod[1].split('d')[1]):
                        mod[0]-=1
                        send_new_message('Usado o recurso '+mod[1]+' na rolagem entre '+clients[rolagem['caller']]['data']+' e '+clients[rolagem['receiver']]['data']+'.',receiver)

def apply_posmod_pos(receiver,fonte,rolagem,r):
    for mod in fonte['posmod']:
        if mod[0]!=0:
            if '/' in mod[1]:
                modsepa=mod[1].split('/')
                for alternativa in modsepa:
                    if 'd' not in alternativa and mod[0]:
                        if r<=rolagem['p'] and '-' in alternativa:
                            if r-Decimal(alternativa)*50>rolagem['p']:
                                mod[0]-=1
                                send_new_message('Usado o recurso '+alternativa+' em '+mod[1]+' na rolagem entre '+clients[rolagem['caller']]['data']+' e '+clients[rolagem['receiver']]['data']+'.',receiver)
                                r-=Decimal(alternativa)*50
                        elif r>rolagem['p'] and '-' not in alternativa:
                            if r-Decimal(alternativa)*50<=rolagem['p']:
                                mod[0]-=1
                                send_new_message('Usado o recurso '+alternativa+' em '+mod[1]+' na rolagem entre '+clients[rolagem['caller']]['data']+' e '+clients[rolagem['receiver']]['data']+'.',receiver)
                                r-=Decimal(alternativa)*50
            else:
                if 'd' not in mod[1]:
                    if r<=rolagem['p'] and '-' in mod[1]:
                        if r-Decimal(mod[1])*50>rolagem['p']:
                            mod[0]-=1
                            send_new_message('Usado o recurso '+mod[1]+' na rolagem entre '+clients[rolagem['caller']]['data']+' e '+clients[rolagem['receiver']]['data']+'.',receiver)
                            r-=Decimal(mod[1])*50
                    elif r>rolagem['p'] and '-' not in mod[1]:
                        if r-Decimal(mod[1])*50<=rolagem['p']:
                            mod[0]-=1
                            send_new_message('Usado o recurso '+mod[1]+' na rolagem entre '+clients[rolagem['caller']]['data']+' e '+clients[rolagem['receiver']]['data']+'.',receiver)
                            r-=Decimal(mod[1])*50
    return(r)

def rola(rolagem):
    global rolls
    if rolagem['ready']!=2:
        return
    caller=rolagem['caller']
    recibru=rolagem['receiver']
    rolls[recibru].pop(0)
    crit=rolagem['p']/10+(rolagem['p']>rolagem['q'])*(rolagem['p']-rolagem['q'])
    apply_posmod_pre(recibru,rolagem,rolagem)
    apply_posmod_pre(caller,rolls[caller],rolagem)
    r=random.randint(1,rolagem['q'])
    r=apply_posmod_pos(recibru,rolagem,rolagem,r)
    r=apply_posmod_pos(caller,rolls[caller],rolagem,r)
    r=apply_posmod_pos(recibru,rolagem,rolagem,r)
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
                        send_new_message(clients[notified_socket]['data']+" desconectou enquanto chamava você. Você não está mais rolando.",client_socket)
                        clients[client_socket]['rolling']=0
                    try:
                        clients[rolls[notified_socket][0]['caller']]['calling'].remove(notified_socket)
                        if clients[rolls[notified_socket][0]['caller']]['calling']==[]:
                            send_new_message(clients[notified_socket]['data']+" desconectou e era sua única chamada. Você não está mais rolando.",rolls[notified_socket][0]['caller'])
                            clients[rolls[notified_socket][0]['caller']]['rolling']=0
                        else:
                            send_new_message(clients[notified_socket]['data']+" desconectou porém você ainda tem chamadas. Você continua rolando.",rolls[notified_socket][0]['caller'])
                    except:
                        pass
                    
                    # Remove from list for socket.socket()
                    sockets_list.remove(notified_socket)

                    # Remove from our list of users
                    del clients[notified_socket]

                    continue

                # Get user by notified socket, so we will know who sent the message
                user = clients[notified_socket]
                messagepf=pickle.loads(message["data"])
                
                if type(messagepf).__name__=='msg':
                    messagepf.cor=user['cor']
                    if not messagepf.destiny:
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
                        aceitos=[]                        
                        if messagepf.who=='hidden':
                            send_new_message("Confira o que você espera enviar ao oponente em caso de sucesso dele (s ou n).",notified_socket)
                        for client_socket in clients:
                            check=clients[client_socket]['data']
                            roladas=messagepf.receiver.count(check)
                            if roladas:
                                if not clients[client_socket]['rolling']:
                                    user['rolling']=1
                                    clients[client_socket]['rolling']+=roladas
                                    aceitos.append(client_socket)
                                    send_new_message(check+" encontra-se disponível.",notified_socket)
                                    send_new_message(user['data']+" iniciou "+str(roladas)+" rolagem(ns) com você com as tags: "+messagepf.who+messagepf.hidden*'e hidden'+(roladas>1)*"\nRecomenda-se ler o resultado anterior para inserir o próximo bloco para evitar repetição de recursos."+"\nBloco da primeira rolagem:",client_socket)
                                    rolls[client_socket]=[{'advan': 0,'receiver': client_socket,'caller': notified_socket,'ready':0,'p':1000,'q':2000,'send_type': messagepf.who}]
                                    for i in range(roladas-1):
                                        rolls[client_socket].append({'advan': 0,'receiver': client_socket,'caller': notified_socket,'ready':0,'p':1000,'q':2000,'send_type': messagepf.who})
                                else:
                                    send_new_message(check+" encontra-se indisponível.",notified_socket)    
                        user['calling']=aceitos
                        if user['rolling']:
                            send_new_message("Bloco comunitário:",notified_socket)
                            rolls[notified_socket]={'send_type':messagepf.who}
                        else:
                            send_new_message("Ninguém aceitou.",notified_socket)

                elif type(messagepf).__name__=='bloco':
                    if user['rolling']:
                        rolls[notified_socket][0]['posmod']=messagepf.posmod
                        if not user['calling']:
                            rolls[notified_socket][0]['premod']=messagepf.premod
                            rolls[notified_socket][0]['ready']+=1
                            rola(rolls[called_socket][0]) 
                        else:
                            if rolls[notified_socket]['send_type']=='hidden':
                                for called_socket in user['calling']:
                                    for i in range(len(rolls[called_socket])):
                                        rolls[called_socket][i]['hidden_message']=messagepf.sn
                            for called_socket in user['calling']:
                                for i in range(len(rolls[called_socket])):
                                    rolls[called_socket][i]['p']+=messagepf.premod
                                    rolls[called_socket][i]['ready']+=1
                                    rola(rolls[called_socket][i]) 
                        user['rolling']-=1
                        user['calling']=[]
                        send_new_message('Premod: '+str(messagepf.premod)+'\nPosmod: '+messagepf.posmod+"\gFinalizado! Mais "+str(user['rolling'])+' rolagens.',notified_socket)
                    else:
                        send_new_message("Você não se encontra rolando no momento.",notified_socket)
                            
            elif notified_socket in espera_de_cor:
                cor=receive_message(notified_socket)
                if cor is False:
                        sockets_list.remove(notified_socket)
                else:
                    for client_socket in clients:
                        send_new_message('O usuário '+espera_de_cor[notified_socket]['data']+' se juntou ao chat!',client_socket)
                    # Save username and username header
                    clients[notified_socket] = espera_de_cor[notified_socket]
                    clients[notified_socket]['calling'] = []
                    clients[notified_socket]['rolling'] = 0
                    clients[notified_socket]['cor']=cor['data'].decode('utf-8')
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
                        
                        login_message='Ok'
                        user['data']=user['data'].decode('utf-8').replace(' ','_')
                        
                        for socket in clients:
                            if user['data'] in clients[socket]['data'] or clients[socket]['data'] in user['data']:
                                login_message='Username semelhante já em uso, tente outro'

                        if login_message=='Ok':
                            if user['data']=='Server' or user['data']=='':
                                login_message='Username não pode ser Server ou ser branco, tente outro'

                        if login_message=='Ok':
                            if '-' in user['data'] or '/' in user['data'] or '\\' in user['data']:
                                login_message='Retire caracteres - e / e \ do username'
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


        elif messagepf.startswith('-dice'):
                        messagepf=messagepf.replace(' ','')
                        messagepf=messagepf.replace('-dice','')
                        messagepf=messagepf.replace('-','+-')
                        soma=0
                        somap='a'
                        dice_box=''
                        try:
                            dice_upper_list=messagepf.split('+')
                            for j in range(len(dice_upper_list)):
                                u=dice_upper_list[j]
                                if u!='':
                                    dice_list=u.split('d')
                                    if len(dice_list)==2:
                                        dice_box+=' \g'
                                        somap=0
                                        litbox='[ '
                                        for i in range(abs(int(dice_list[0]))):
                                            d=random.randint(1,abs(int(dice_list[1])))
                                            if '-' not in u:
                                                somap+=d
                                                litbox+='+'+str(d)+' '
                                            else:
                                                somap-=d
                                                litbox+='-'+str(d)+' '
                                        litbox+=']'
                                        dice_box+=litbox
                                        soma+=somap
                                        if j+1<len(dice_upper_list):
                                            if 'd' in dice_upper_list[j+1]: 
                                                dice_box+=' = '+'+'*(somap>=0)+str(somap)
                                    else:
                                        soma+=int(dice_list[0])
                                        dice_box+=' '+'+'*('-' not in u)+dice_list[0]
                                        if somap!='a':
                                                somap+=int(dice_list[0])
                                                if j+1<len(dice_upper_list):
                                                    if 'd' in dice_upper_list[j+1]: 
                                                        dice_box+=' = '+'+'*(somap>=0)+str(somap)
                                                else:
                                                    dice_box+=' = '+'+'*(somap>=0)+str(somap)
                            if dice_box.endswith(']'):
                                dice_box+=' = '+'+'*(somap>=0)+str(somap)
                            messagepf=messagepf.replace('+-','-')
                            if dice_box.startswith(' ') and not dice_box.startswith(' \g'):
                                dice_box=dice_box[1:]
                                dice_box=' \g'+dice_box
                            send_new_message(messagepf+':'+dice_box+' \gTotal: '+str(soma),notified_socket)
                            print(clients[notified_socket]['data']+' rolou: '+messagepf+':'+dice_box+' \gTotal: '+str(soma))
                        except:
                            send_new_message("Algo deu errado, confira seu envio e reenvie.",notified_socket)
                    elif messagepf.startswith('-init'):
                        try:
                            messagepf=messagepf.replace(' ','')
                            messagepf=messagepf.replace('-init','')
                            a=int(messagepf.split('x')[0])
                            b=int(messagepf.split('x')[1])
                            if a<b:
                                a,b=b,a
                            lis_b=[0]*b
                            i=0
                            st=''
                            for u in range(int(a//b+1)):
                                for j in range(b):
                                    if i==a:
                                        break
                                    i+=1
                                    lis_b[j]+=1
                            while len(lis_b):
                                j=random.randint(0,len(lis_b)-1)
                                ind=lis_b.pop(j)
                                st+='▘'+ind*'▖'
                            ordem=random.randint(0,len(st)-1)
                            st=st[ordem:len(st)]+st[0:ordem]
                            for client_socket in clients:
                                send_new_message("Ordem de iniciativa de "+str(a)+' ▞ '+str(b)+' >\n'+str(st),client_socket)
                        except:
                            send_new_message("Algo deu errado, confira seu envio e reenvie.",notified_socket)


