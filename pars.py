from importlib import import_module
import struct
import re
from hp.mpyq import mpyq
from hp import protocol29406

gametypes = {
    50001: 'QuickMatch',
    50021: 'Versus AI',
    50041: 'Practice',
    50031: 'Brawl',
    50051: 'Unranked',
    50061: 'Hero League',
    50071: 'Team League',
}

archive = mpyq.MPQArchive("Blackheart's Bay.StormReplay")
header = protocol29406.decode_replay_header(archive.header['user_data_header']['content'])
baseBuild = header['m_version']['m_baseBuild']
protocol = import_module('hp.protocol%s' % baseBuild,)
initdata = protocol.decode_replay_initdata(archive.read_file('replay.initData'))
details = protocol.decode_replay_details(archive.read_file('replay.details'))
attributes = protocol.decode_replay_attributes_events(archive.read_file('replay.attributes.events'))
lobby_data = archive.read_file('replay.server.battlelobby')

def get_playerlevel_or_tag(lobby_data, playername, mode = 0):
    tag = ""
    to_search = r'%s#(\d{4,8})' % playername
    r = re.compile(to_search)
    s = r.search(lobby_data)
    if s:
        tag = "%s#%s" % (playername, s.groups(0)[0])
        player_level = struct.unpack(">i", lobby_data[s.end():s.end()+4])[0]
    if mode:
        return tag
    else:
        return player_level


gametypeID = initdata['m_syncLobbyState']['m_gameDescription']['m_gameOptions']['m_ammId']
print(details['m_title'] +' - '+ gametypes[gametypeID])

if details['m_playerList'][0]['m_result'] == 2:
    print('Firts 5 players won.')
else:
    print('The last 5 players won.')

for p in range(10):
    name = details['m_playerList'][p]['m_name']
    hero = details['m_playerList'][p]['m_hero']
    playerlevel = get_playerlevel_or_tag(lobby_data, name)
    herolevel = attributes['scopes'][p+1][4008][0]['value'].strip()
    print('level ' + str(playerlevel) + ' ' + name + ' played ' + hero + ' (level ' + herolevel + ')')