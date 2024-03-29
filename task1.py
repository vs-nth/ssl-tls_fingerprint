from scapy.all import *
from graphviz import Digraph
from copy import deepcopy

f = rdpcap('handshake_packets.pcap')

dict_of_handshakes = {}

handshake_record_table = {0: '0x00', 1: '0x01', 2: '0x02', 11: '0x0b',
                          12: '0x0c', 13: '0x0d', 14: '0x0e', 15: '0x0f',
                          16: '0x10', 20: '0x14'}

matrix_handshake_table = {0: 0, 1: 1, 2: 2, 11: 3,
                          12: 4, 13: 5, 14: 6, 15: 7,
                          16: 8, 20: 9, 4: 12}
ports = {}


class Handshake:

    def __init__(self, packet):
        self.src = packet[IP].src
        self.dst = packet[IP].dst
        self.dport = str(packet[TCP].dport)
        self.sport = str(packet[TCP].sport)
        #self.hash_val = self.src + '-' + self.sport + '-' + self.dst + '-' + self.dport
        self.hash_val = self.dport if self.sport == '443' else self.sport
        self.previous_state = None
        self.current_state = None
        self.matrix = [[0 for x in range(14)] for y in range(14)]
        self.counter = 0

# 0- hello request  1 - client hello   2- server hello   3-certificate
# 4-server_KE    5-cert_req    6-server_done   7-cert_verif  8-clientKE
# 9-finish   10-Change Cipher spec   11- Application Data    12- Alert
# 13- New session ticket

table= {'22.0': 0, '22.1': 1, '22.2': 2, '22.11': 3, '22.12':4, '22.13':5, '22.14': 6,
        '22.15': 7, '22.16' : 8, '22.20': 9, '20': 10, '23' : 11, '21': 12, '22.4': 13}
count = 0

for packet in f:
    count += 1
    if packet.haslayer(SSL):
        handshake_packet = Handshake(packet)
        if handshake_packet.hash_val in list(dict_of_handshakes.keys()):
            handshake_packet.previous_state = dict_of_handshakes[handshake_packet.hash_val].previous_state
            handshake_packet.matrix = deepcopy(dict_of_handshakes[handshake_packet.hash_val].matrix)
        else:
            dict_of_handshakes[handshake_packet.hash_val] = handshake_packet
        handshake_packet.counter += 1
        for record in packet.records:
            if record.content_type in [20,21,22,23]:
                if record.content_type == 22:  # handshake protocol
                    if not record.haslayer(TLSCiphertext) and record[TLSHandshake].type != 22 and record[TLSHandshake].type != 0: # not Certificate Status and encrypted handshake message
                        #handshake_packet.current_state = matrix_handshake_table[record[TLSHandshake].type]
                        val = str(record.content_type)+'.'+str(record[TLSHandshake].type)
                        handshake_packet.current_state = table[str(record.content_type)+'.'+str(record[TLSHandshake].type)]
                elif record.content_type == 20:  # change cipher spec
                    val = str(record.content_type)
                    handshake_packet.current_state = table[str(record.content_type)]
                elif record.content_type == 21:  # alert
                    val = str(record.content_type)
                    handshake_packet.current_state = table[str(record.content_type)]
                elif record.content_type == 23:  # data
                    val = str(record.content_type)
                    handshake_packet.current_state = table[str(record.content_type)]
                #print('count', count, 'previous: ', handshake_packet.previous_state, ' current: ', handshake_packet.current_state, ' val: ', val)
                if handshake_packet.current_state is not None:
                    if handshake_packet.previous_state is None:
                        handshake_packet.matrix[0][0] += 1
                    else:
                        #print('pval: ', handshake_packet.previous_state, ' cval: ', val, 'm[i][j]: ', handshake_packet.matrix[handshake_packet.previous_state][handshake_packet.current_state])
                        handshake_packet.matrix[handshake_packet.previous_state][handshake_packet.current_state] += 1
                    handshake_packet.previous_state = handshake_packet.current_state
                    dict_of_handshakes[handshake_packet.hash_val] = handshake_packet

            # if handshake_packet.previous_state is not None:
            #     if handshake_packet.current_state is not None:
            #         handshake_packet.matrix[handshake_packet.current_state][handshake_packet.previous_state] += 1
            #     else:
            #         continue
            # else:
            #     handshake_packet.matrix[0][0] += 1
            # handshake_packet.previous_state = handshake_packet.current_state
            # dict_of_handshakes[handshake_packet.hash_val] = handshake_packet
            # if handshake_packet.previous_state is None and record[TLSHandshake].type == 1:
            #     handshake_packet.matrix[0][0] += 1
            #     handshake_packet.previous_state = handshake_packet.current_state
            #     dict_of_handshakes[handshake_packet.hash_val] = handshake_packet
            # else:
            #     if handshake_packet.current_state is not None:
            #         handshake_packet.matrix[handshake_packet.current_state][handshake_packet.previous_state] += 1
            #     else:
            #         continue
            # handshake_packet.previous_state = handshake_packet.current_state
            # dict_of_handshakes[handshake_packet.hash_val] = handshake_packet


def normalize(handshake_packet):
    for i in range(14):
        c = 0
        for j in range(14):
            c += handshake_packet.matrix[i][j]
        for j in range(14):
            if c!=0:
                handshake_packet.matrix[i][j] = round(handshake_packet.matrix[i][j]/c, 2)


# 0- hello request  1 - client hello   2- server hello   3-certificate
# 4-server_KE    5-cert_req    6-server_done   7-cert_verif  8-clientKE
# 9-finish   10-Change Cipher spec   11- Application Data    12- Alert
# 13- New session ticket

dot_matrix = {1: 'A', 2 : 'B', 3: 'C', 4 : 'D', 5 : 'E', 6 : 'F', 7 : 'G', 8: 'H',
              9: 'I', 10: 'J', 11: 'K', 12: 'L', 13: 'M', 14: 'O'}


def draw_dot(handshake_packet):
    file = handshake_packet.src + '-' + handshake_packet.sport \
           + '-' + handshake_packet.dst + '-' + handshake_packet.dport
    dot = Digraph(comment='', filename=file)
    dot.node('A', 'Start')
    dot.node('B', '22.1')
    dot.node('C', '22.2')
    dot.node('D', '22.11')
    dot.node('E', '22.12')
    dot.node('F', '22.13')
    dot.node('G', '22.14')
    dot.node('H', '22.15')
    dot.node('I', '22.16')
    dot.node('J', '22.20')
    dot.node('K', '20')
    dot.node('L', '21')
    dot.node('M', '23')
    dot.node('O', '22.4')
    dot.edge('A', 'B')
    for i in range(14):
        for j in range(14):
            if handshake_packet.matrix[i][j] > 0:
                # print(handshake_packet.matrix[i][j])
                lbl = str(handshake_packet.matrix[i][j] * 100) + '%'
                if dot_matrix[i+1] != dot_matrix[j+1]:
                    dot.edge(dot_matrix[i+1], dot_matrix[j+1], label=lbl)
    # print(dot.source)
    #dot.view()
    dot.render('test-output/' + file + '.gv')


for i in list(dict_of_handshakes.keys()):
    #print(dict_of_handshakes[i].matrix)
    normalize(dict_of_handshakes[i])
    #print(dict_of_handshakes[i].matrix)
    draw_dot(dict_of_handshakes[i])

#draw_dot(dict_of_handshakes['45486'])
#dot.render('test-output/round-table.gv', view=True)


