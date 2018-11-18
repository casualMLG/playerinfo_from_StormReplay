from importlib import import_module
import struct
import re
from heroprotocol.mpyq import mpyq
from heroprotocol import protocol29406

gametypes = {
    50001: 'QuickMatch',
    50021: 'Versus AI',
    50041: 'Practice',
    50031: 'Brawl',
    50051: 'Unranked',
    50061: 'Hero League',
    50071: 'Team League',
}

def read_and_decode(filename):
    global initdata, details, attributes, lobby_data
    archive = mpyq.MPQArchive(filename)
    header = protocol29406.decode_replay_header(archive.header['user_data_header']['content'])
    baseBuild = header['m_version']['m_baseBuild']
    protocol = import_module('heroprotocol.protocol%s' % baseBuild,)
    initdata = protocol.decode_replay_initdata(archive.read_file('replay.initData'))
    details = protocol.decode_replay_details(archive.read_file('replay.details'))
    attributes = protocol.decode_replay_attributes_events(archive.read_file('replay.attributes.events'))
    lobby_data = archive.read_file('replay.server.battlelobby') #loby_data is not decoded file content

read_and_decode("Blackheart's Bay.StormReplay")

def get_playerlevel_or_tag(playername, get_tag = 0):
    tag = ""
    to_search = r'%s#(\d{4,8})' % playername
    r = re.compile(to_search)
    s = r.search(lobby_data) #returns a match object. s.end() returns the end index of the match in stream
    if s:
        tag = "%s#%s" % (playername, s.groups(0)[0])
        player_level = struct.unpack(">i", lobby_data[s.end():s.end()+4])[0] #convert 4 bytes after match
    if get_tag:
        return tag
    else:
        return player_level

def did_player_win(list_index):
    if details['m_playerList'][list_index]['m_result'] == 2:
        return True
    return False

def get_gametype():
    gametypeID = initdata['m_syncLobbyState']['m_gameDescription']['m_gameOptions']['m_ammId']
    return gametypes[gametypeID]

def get_map():
    return details['m_title']

def get_player_name(list_index):
    return details['m_playerList'][list_index]['m_name']

def get_hero(list_index):
    return details['m_playerList'][list_index]['m_hero']

def get_herolevel(list_index): #starts from 1 instead of 0
    return int(attributes['scopes'][list_index+1][4008][0]['value'].strip())

print(get_map() +' - '+ get_gametype())

if did_player_win(0):
    print('Firts 5 players won.')
else:
    print('The last 5 players won.')

for player_index in range(10):
    name = get_player_name(player_index)
    hero = get_hero(player_index)
    playerlevel = get_playerlevel_or_tag(name)
    herolevel = get_herolevel(player_index)
    print('level ' + str(playerlevel) + ' ' + name + ' played ' + hero + ' (level ' + str(herolevel) + ')')
