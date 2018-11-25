from importlib import import_module
from struct import unpack
from glob import glob
import re
from heroprotocol.mpyq import mpyq
from heroprotocol import protocol29406
from filetimes import filetime_to_dt

gametypes = {
    50001: 'QuickMatch',
    50021: 'VersusAI',
    50041: 'Practice',
    50031: 'Brawl',
    50051: 'Unranked',
    50061: 'Hero League',
    50071: 'Team League',
}
regions = {1: 'US', 2: 'EU', 3: 'KR', 5: 'CN'}

def read_and_decode(filename, do_attributes = 1, do_initdata = 1):
    global initdata, details, attributes, lobby_data
    archive = mpyq.MPQArchive(filename)
    header = protocol29406.decode_replay_header(archive.header['user_data_header']['content'])
    baseBuild = header['m_version']['m_baseBuild']
    protocol = import_module('heroprotocol.protocol%s' % baseBuild,)
    details = protocol.decode_replay_details(archive.read_file('replay.details'))
    lobby_data = archive.read_file('replay.server.battlelobby') #loby_data is not decoded file content
    if do_initdata: # for game type
        initdata = protocol.decode_replay_initdata(archive.read_file('replay.initData'))
    if do_attributes: # for hero level
        attributes = protocol.decode_replay_attributes_events(archive.read_file('replay.attributes.events'))

def get_playerlevel_or_tag(playername, get_tag = 0):
    if not lobby_data:
        return 0
    tag = ""
    to_search = r'%s#(\d{4,8})' % playername
    r = re.compile(to_search)
    s = r.search(lobby_data) #returns a match object. s.end() returns the end index of the match in string
    if s:
        tag = "%s#%s" % (playername, s.groups(0)[0])
        player_level = unpack(">i", lobby_data[s.end():s.end()+4])[0] #convert 4 bytes after match
    if get_tag:
        return tag
    else:
        return player_level

def did_player_win(list_index):
    if details['m_playerList'][list_index]['m_result'] == 2:
        return True
    return False

def get_region(list_index):
    regionID = details['m_playerList'][list_index]['m_toon']['m_region']
    if regionID in regions:
        return regions[regionID]
    return regionID

def get_gametype(id = 0):
    gametypeID = initdata['m_syncLobbyState']['m_gameDescription']['m_gameOptions']['m_ammId']
    if id:
        return gametypeID
    return gametypes[gametypeID]

def get_map():
    return details['m_title'] #language specific

def get_date():
    return filetime_to_dt(details['m_timeUTC']).date()

def get_player_name(list_index):
    return details['m_playerList'][list_index]['m_name']

def get_hero(list_index):
    return details['m_playerList'][list_index]['m_hero'] #language specific

def get_herolevel(list_index): #starts from 1 instead of 0
    return int(attributes['scopes'][list_index+1][4008][0]['value'].strip())

def make_database(folder, use_attributes = 1, use_initdata = 1 ):
    databases = {
        50001: open(folder + '_qm_database.txt', 'a'),
        50051: open(folder + '_ud_database.txt', 'a'),
        50061: open(folder + '_hl_database.txt', 'a'),
        50071: open(folder + '_tl_database.txt', 'a')
    }
    count = 1
    failed = 0
    file_list = glob("replays/" + folder + "/*.StormReplay")
    last_file = len(file_list)
    for file in file_list:
        read_and_decode(file, use_attributes, use_initdata)
        type = get_gametype(1)
        if type in databases:
            team1 = []
            team2 = []
            for player_index in range(10):
                name = get_player_name(player_index)
                playerlevel = get_playerlevel_or_tag(name)
                if playerlevel < 1 or playerlevel > 5000:
                    team1 = [0]
                    failed += 1
                    break
                herolevel = get_herolevel(player_index)
                if player_index < 5:
                    team1.extend([playerlevel, herolevel])
                else:
                    team2.extend([playerlevel, herolevel])
            if team1[0]:
                if did_player_win(0):
                    levels = team1 + team2
                else:
                    levels = team2 + team1
                line = ','.join(map(str, levels))
                if count != last_file:
                    line += '\n'
                databases[type].write(line)
        if count % 10 == 0:
            print str(count)+'\r',
        count += 1
    for f in databases:
        databases[f].close()
    print('\n' + str(count - failed) + ' out of ' + str(count) + ' Successful. Failed:' + str(failed))

def test_folder(folder):
    HL=TL=other_type=us=eu=other_region=0
    for file in glob("replays/" + folder + "/*.StormReplay"):
        read_and_decode(file, 0, 1)
        t = get_gametype()
        if t == 'Hero League':
            HL += 1
        elif t == 'Team League':
            TL += 1
        else:
            other_type += 1
        r = get_region(0)
        if r == 'US':
            us += 1
        elif r == 'EU':
            eu += 1
        else:
            other_region += 1
    print('Hero league: ' + str(HL) + '\nTeam League: ' + str(TL) + '\nOther game types: ' + str(other_type) +
          '\n\nUS: ' + str(us) + '\nEU: ' + str(eu) + '\nOther regions: ' + str(other_region))

def test_file(folder, file_index = 0):
    read_and_decode(glob("replays/" + folder + "/*.StormReplay")[file_index])
    print(get_gametype() + ' - ' + get_map() + ' - ' + str(get_date()))
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

make_database('test')
#test_file('muu',2)
#test_folder('muu')