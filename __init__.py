''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on githab.com)
Version:
    '0.7.0 2015-12-11'
ToDo: (see end of file)
'''

import  os, json, random, subprocess, shlex
import  cudatext        as app
from    cudatext    import ed
import  cudatext_cmd    as cmds
import  cudax_lib       as apx
from    cudax_lib   import log

pass;                           # Logging
pass;                           LOG = (-2==-2)  # Do or dont logging.

JSON_FORMAT_VER = '20151209'
EXTS_JSON       = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'exttools.json'

RSLT_TO_PANEL   = 'Output panel'
RSLT_TO_PANEL_AP= 'Output panel (append)'
RSLT_TO_NEWDOC  = 'Copy to new document'
RSLT_TO_CLIP    = 'Copy to clipboard'
RSLT_REPL_SEL   = 'Replace selection'

class Command:
    exts        = []    # Main list [exttools]
    ext4id      = {}    # Derived dict {id:exttool}
    
#   id_menu     = 0
    
    def __init__(self):
        ver_exts    = apx._json_loads(open(EXTS_JSON).read()) if os.path.exists(EXTS_JSON) else {'ver':JSON_FORMAT_VER, 'list':[]}
        if ver_exts['ver'] < JSON_FORMAT_VER:
            # Adapt to new format
            pass
        self.exts   = ver_exts['list']
        self.ext4id = {str(ext['id']):ext for ext in self.exts}
       #def __init__
       
    def on_start(self, ed_self):
        pass
        self._do_acts(acts='|reg|menu|')
       #def on_start
        
    def _adapt_menu(self):
        ''' Add or change top-level menu ExtTools
        '''
        id_menu     = 0
        if 'exttools_id_menu' in dir(ed):               ##?? dirty hack!
            id_menu = ed.exttools_id_menu               ##?? dirty hack!
            # Clear old
            app.app_proc(app.PROC_MENU_CLEAR, id_menu)
        else:
#       if 0==self.id_menu:
            # Create AFTER Plugins
            top_nms = app.app_proc(app.PROC_MENU_ENUM, 'top').splitlines()
            pass;              #LOG and log('top_nms={}',top_nms)
            plg_ind = top_nms.index('&Plugins|')        ##?? 
            id_menu = app.app_proc( app.PROC_MENU_ADD, '{};{};{};{}'.format('top', 0, '&Tools', 1+plg_ind))
            ed.exttools_id_menu = id_menu               ##?? dirty hack!

        # Fill
        app.app_proc(app.PROC_MENU_ADD, '{};cuda_exttools,dlg_config;{}'.format(id_menu, 'Con&fig...'))
        if 0==len(self.exts):
            return
        app.app_proc(app.PROC_MENU_ADD, '{};;-'.format(id_menu))
        for ext in self.exts:
            app.app_proc(app.PROC_MENU_ADD, '{};cuda_exttools,run,{};{}'.format(id_menu, ext['id'], ext['nm']))
       #def _adapt_menu
        
    def dlg_config(self):
        ''' Show dlg for change exts list.
        '''
        acts= ['Edit Tool...'
              ,'Hotkeys for Tool...'
              ,'Run Tool...'
              ,'Delete Tool...'
              ,'-----'
              ,'Help...'
              ,'-----'
              ,'Add Tool...'
              ]
        while True:
            act_ind = app.dlg_menu(app.MENU_LIST, '\n'.join(acts))
            if act_ind is None or acts[act_ind][0]=='-': return
            act     = acts[act_ind]
            act     = act[:(act+' ').index(' ')]    # first word

            if act=='Help...':
                l   = chr(13)
                app.msg_box( ''
                    +   'In "File for call" and "Params for call" fields of external tools configuration'
                    +   ' the following macros are allowed.'
                    +l+ ''
                    +l+ 'Currently focused file properties:'
                    +l+ '  {FileName} - full path'
                    +l+ '  {FileDir} - folder path, without file name'
                    +l+ '  {FileNameOnly} - name only, without folder path'
                    +l+ '  {FileNameNoExt} - name without extension and path'
                    +l+ '  {FileExt} - extension'
                    +l+ ''
                    +l+ 'Currently focused editor properties (for top caret):'
                   #+l+ '  {CurrentWord}'
                    +l+ '  {CurrentLine}'
                    +l+ '  {CurrentLineNum}'
                    +l+ '  {CurrentColumnNum}'
                    +l+ '  {SelectedText}' 
                    +l+ ''
                    +l+ 'Prompted:'
                    +l+ '  {Interactive} - Some text'
                    +l+ '  {InteractiveFile} - Some file name '
                    , app.MB_OK)
                continue # while

            nms         = [ext['nm'] for ext in self.exts]

            if act=='Add':
                file4run= app.dlg_file(True, '!', '', '')   # '!' to disable check "filename exists"
                ext     = self._dlg_edit_ext('New Tool properties'
                        ,   {'id':random.randint(100000, 999999)
                            ,'file':file4run if file4run is not None else ''
                            }
                        ,   nms)
                if ext is None: return
                self.exts   += [ext]
                self._do_acts('add')
                continue # while

            keys_json   = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'keys.json'
            keys        = apx._json_loads(open(keys_json).read()) if os.path.exists(keys_json) else {}
            kys         = []
            for ext in self.exts:
                ext_key = 'cuda_exttools,run,{}'.format(ext['id'])
                ext_keys= keys.get(ext_key, {})
                kys    += ['/'.join([' * '.join(ext_keys.get('s1', []))
                                    ,' * '.join(ext_keys.get('s2', []))
                                    ]).strip('/')
                          ]
            
            ext     = ''
            if False:pass
            elif 1==len(nms):
                ext_ind = 0
            else:
                ext_ind = app.dlg_menu(app.MENU_LIST
                        , '\n'.join('{}: {}\t{}'.format(a,n,k) for (a,n,k) in list(zip([act]*len(nms), nms, kys)))
                        )
                if ext_ind is None: continue # while

            ext     = self.exts[ext_ind]
            ext_keys= '('+kys[ext_ind]+')' if ''!=kys[ext_ind] else ''

            what    = ''        
            if False:pass
            elif act=='Delete': 
                #Delete
                if app.msg_box( 'Delete Tool\n    {} {}'.format(
                                nms[ext_ind]
                              , ext_keys)
                              , app.MB_YESNO)!=app.ID_YES:  continue # while
                what    = 'delete:'+str(ext['id'])
                del self.exts[ext_ind]

            elif act=='Hotkeys':
                app.dlg_hotkeys('cuda_exttools,run,'+str(ext['id']))

            elif act=='Edit': 
                #Edit
                ext     = self._dlg_edit_ext('Tool properties', ext, nms)

            self._do_acts(what)
#           break #while
           #while
       #def dlg_config
       
    def _do_acts(self, what='', acts='|save|second|reg|keys|menu|'):
        ''' Use exts list '''
        pass;                  #LOG and log('what, acts={}',(what, acts))
        # Save
        if '|save|' in acts:
            open(EXTS_JSON, 'w').write(json.dumps({'ver':JSON_FORMAT_VER, 'list':self.exts}, indent=4))
        
        # Secondary data
        if '|second|' in acts:
            self.ext4id     = {str(ext['id']):ext for ext in self.exts}
        
        # Register new subcommands
        if '|reg|' in acts:
            reg_subs        = 'cuda_exttools;run;{}'.format('\n'.join(
                             'exttool: {}\t{}'.format(ext['nm'],ext['id']) 
                                 for ext in self.exts)
                             )
            pass;              #LOG and log('reg_subs={}',reg_subs)
            app.app_proc(app.PROC_SET_SUBCOMMANDS, reg_subs)
        
        # Clear keys.json
        if '|keys|' in acts and ':' in what:
            # Need delete a key 'cuda_exttools,run,NNNNN'
            ext_id      = what[1+what.index(':'):]
            ext_key     = 'cuda_exttools,run,{}'.format(ext_id)
            keys_json   = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'keys.json'
            if not os.path.exists(keys_json): return
            keys        = apx._json_loads(open(keys_json).read())
            pass;              #LOG and log('??? key={}',ext_key)
            if keys.pop(ext_key, None) is not None:
                pass;           LOG and log('UPD keys.json, deleted key={}',ext_key)
                open(keys_json, 'w').write(json.dumps(keys, indent=2))
        
        # [Re]Build menu
        if '|menu|' in acts:
            self._adapt_menu()
       #def _do_acts

    def run(self, ext_id):
        ''' Main (and single) way to run any exttool
        '''
        ext_id  = str(ext_id)
        pass;                  #LOG and log('ext_id={}',ext_id)
        ext     = self.ext4id.get(str(ext_id))
        if ext is None:
            return app.msg_status('No Tool: {}'.format(ext_id))
        cmnd    = ext['file']
        prms    = ext['prms']
        pass;                   LOG and log('nm="{}", cmnd="{}", raw-prms="{}"',ext['nm'], cmnd, prms)
        
        # Preparing
        file_nm = ed.get_filename()
        if '{FileName}'         in prms: prms = prms.replace('{FileName}'     ,quot(                          file_nm)                  )
        if '{FileDir}'          in prms: prms = prms.replace('{FileDir}'      ,quot(          os.path.dirname(file_nm))                 )
        if '{FileNameOnly}'     in prms: prms = prms.replace('{FileNameOnly}' ,quot(         os.path.basename(file_nm))                 )
        if '{FileNameNoExt}'    in prms: prms = prms.replace('{FileNameNoExt}',quot('.'.join(os.path.basename(file_nm).split('.')[0:-1])))
        if '{FileExt}'          in prms: prms = prms.replace('{FileExt}'      ,quot(         os.path.basename(file_nm).split('.')[-1])  )

        (cCrt, rCrt
        ,cEnd, rEnd)    = ed.get_carets()[0]
        if '{CurrentLine}'      in prms: prms = prms.replace('{CurrentLine}'     , quot(ed.get_text_line(rCrt)))
        if '{CurrentLineNum}'   in prms: prms = prms.replace('{CurrentLineNum}'  , str(1+rCrt))
        if '{CurrentColumnNum}' in prms: prms = prms.replace('{CurrentColumnNum}', str(1+ed.convert(app.CONVERT_CHAR_TO_COL, cCrt, rCrt)[0]))
        if '{SelectedText}'     in prms: prms = prms.replace('{SelectedText}'    , quot(ed.get_text_sel()))

        if '{Interactive}' in prms:
            ans = app.dlg_input('Param for call {}'.format(ext['nm']), '')
            ans = '' if ans is None else ans
            prms = prms.replace('{Interactive}'     , quot(ans))
        if '{InteractiveFile}' in prms:
            ans = app.dlg_file(True, '!', '', '')   # '!' to disable check "filename exists"
            ans = '' if ans is None else ans
            prms = prms.replace('{InteractiveFile}' , quot(ans))
        
        pass;                   LOG and log('ready prms={}',(prms))

        # Calling
        if 'Y'  ==ext.get('savs', 'N'):
            if not ed.file_save():  return
        if 'ALL'==ext.get('savs', 'N'):
            ed.cmd(cmds.cmd_FileSaveAll)
        
#       val4call  = (cmnd+' '+prms).strip()
#       val4call  = [(cmnd+' '+prms).strip()]
#       val4call  = [cmnd, prms]
        val4call  = [cmnd] + shlex.split(prms)
#       val4call  = [cmnd] + list(map(lambda t: 'r"'+t+'"', shlex.split(prms)))
        pass;                   LOG and log('val4call={}',(val4call))
        if 'Y'!=ext.get('capt', 'N'):
            # Without capture
            subprocess.Popen(val4call)
#           subprocess.Popen([cmnd, prms])
            return
        
        # With capture
        pass;                  #LOG and log('?? Popen',)
#       pipe    = subprocess.Popen([cmnd, prms]
        pipe    = subprocess.Popen(val4call
                                , stdout=subprocess.PIPE
                                , stderr=subprocess.STDOUT
                               #, universal_newlines = True
                                , shell=True)
        if pipe is None:
            pass;              #LOG and log('fail Popen',)
            app.msg_status('Fail call: {} {}'.format(cmnd, prms))
            return
        pass;                  #LOG and log('ok Popen',)
        app.msg_status('Call: {} {}'.format(cmnd, prms))

        rslt    = ext.get('rslt', RSLT_TO_PANEL)
        rslt_txt= ''
        if False:pass
        elif rslt in (RSLT_TO_PANEL, RSLT_TO_PANEL_AP):
            ed.cmd(cmds.cmd_ShowPanelOutput)
            app.app_log(app.LOG_SET_PANEL, app.LOG_PANEL_OUTPUT)
            if rslt==RSLT_TO_PANEL:
                app.app_log(app.LOG_CLEAR, '')
        elif rslt ==  RSLT_TO_NEWDOC:
            app.file_open('')
            
        while True:
            out_ln = pipe.stdout.readline().decode(ext.get('encd', 'utf-8'))
            if 0==len(out_ln): break
            out_ln = out_ln.strip('\r\n')
            pass;              #LOG and log('out_ln={}',out_ln)
            if False:pass
            elif rslt in (RSLT_TO_PANEL, RSLT_TO_PANEL_AP):
                app.app_log(app.LOG_ADD, out_ln)
            elif rslt ==  RSLT_TO_NEWDOC:
                ed.set_text_line(-1, out_ln)
            elif rslt in (RSLT_TO_CLIP
                         ,RSLT_REPL_SEL):
                rslt_txt+= out_ln + '\n'
           #while True

        rslt_txt= rslt_txt.strip('\n')
        if False:pass
        elif rslt == RSLT_TO_CLIP:
            app.app_proc(app.PROC_SET_CLIP, rslt_txt)
        elif rslt == RSLT_REPL_SEL:
            crts    = ed.get_carets()
            for icrt in range(len(crts)-1, -1, -1):
                (cCrt, rCrt
                ,cEnd, rEnd)    = crts[icrt]
                if -1!=cEnd:
                    (rCrt, cCrt), (rEnd, cEnd) = apx.minmax((rCrt, cCrt), (rEnd, cEnd))
                    ed.delete(cCrt, rCrt, cEnd, rEnd)
                ed.insert(cCrt, rCrt, rslt_txt)
       #def run
       
    def _dlg_edit_ext(self, title, ext_dict, used_nms):
        NM  = 0
        FILE= 1
        PRMS= 2
        DDIR= 3
        SAVS= 4
        CAPT= 5
        ENCD= 6
        RSLT= 7
        CNT = 8
        ext_list       = list(range(CNT))
        ext_list[NM  ] = ext_dict.get('nm'  , '') 
        ext_list[FILE] = ext_dict.get('file', '')
        ext_list[PRMS] = ext_dict.get('prms', '')
        ext_list[DDIR] = ext_dict.get('ddir', '')
        ext_list[SAVS] = ext_dict.get('savs', 'N')
        ext_list[CAPT] = ext_dict.get('capt', 'N')
        ext_list[ENCD] = ext_dict.get('encd', '')
        ext_list[RSLT] = ext_dict.get('rslt', '')
        while True:
            ext_list = app.dlg_input_ex(CNT, title
                    , '*Name'                       , ext_list[NM  ]
                    , '*File (or command) to call'  , ext_list[FILE]
                    , 'Params for call'             , ext_list[PRMS]
                    , 'Default folder'              , ext_list[DDIR]
                    , 'Save before (N/Y/ALL)'       , ext_list[SAVS]
                    , 'Capture output (N/Y)'        , ext_list[CAPT]
                    , 'Encoding (empty to pick)'    , ext_list[ENCD]
                    , 'Output usage (empty to pick)', ext_list[RSLT]
                    )
            if ext_list is None: return None

            if ext_list[NM] in used_nms and ext_list[NM]!=ext_dict.get('nm', ''):
                app.msg_box('Choose a name different from:\n    '+'\n    '.join(used_nms), app.MB_OK)
                continue

            if ext_list[CAPT] == 'Y' and ext_list[ENCD] == '':
                enc_nms = self.get_encoding_names()
                enc_ind = app.dlg_menu(app.MENU_LIST_ALT, '\n'.join(enc_nms))
                if enc_ind is not None:
                    ext_list[ENCD] = enc_nms[enc_ind].split('\t')[0]
                else:
                    ext_list[ENCD] = enc_nms[0      ].split('\t')[0]
                continue
        
            if ext_list[CAPT] == 'Y' and ext_list[RSLT] == '':
                usg_nms = self.get_usage_names()
                usg_ind = app.dlg_menu(app.MENU_LIST, '\n'.join(usg_nms))
                if usg_ind is not None:
                    ext_list[RSLT] = usg_nms[usg_ind]
                else:
                    ext_list[RSLT] = usg_nms[0]
                continue
        
            if ext_list[NM] != '' and ext_list[FILE] != '': break
           #while True
        ext_dict['nm']      = ext_list[NM  ]
        ext_dict['file']    = ext_list[FILE]
        ext_dict['prms']    = ext_list[PRMS]
        ext_dict['ddir']    = ext_list[DDIR]
        ext_dict['savs']    = ext_list[SAVS]
        ext_dict['capt']    = ext_list[CAPT]
        ext_dict['encd']    = ext_list[ENCD]
        ext_dict['rslt']    = ext_list[RSLT]
        return ext_dict
       #def _dlg_edit_ext
       
    def get_encoding_names(self):
        return [
            'mbcs\tWindows only: Encode operand according to the ANSI codepage (CP_ACP, dbcs)'
        ,   'cp866\tRussian (DOS)'
        ,   'utf_8\tall language'
        ,   'ascii\tEnglis'
        ,   'cp037\tEnglis'
        ,   'cp424\tHebre'
        ,   'cp437\tEnglis'
        ,   'cp500\tWestern Europ'
        ,   'cp737\tGree'
        ,   'cp775\tBaltic language'
        ,   'cp850\tWestern Europ'
        ,   'cp852\tCentral and Eastern Europ'
        ,   'cp855\tBulgarian, Byelorussian, Macedonian, Russian, Serbia'
        ,   'cp856\tHebre'
        ,   'cp857\tTurkis'
        ,   'cp858\tWestern Europ'
        ,   'cp860\tPortugues'
        ,   'cp861\tIcelandi'
        ,   'cp862\tHebre'
        ,   'cp863\tCanadia'
        ,   'cp865\tDanish, Norwegia'
        ,   'cp869\tGree'
        ,   'cp875\tGree'
        ,   'cp1026\tTurkis'
        ,   'cp1140\tWestern Europ'
        ,   'cp1250\tCentral and Eastern Europ'
        ,   'cp1251\tBulgarian, Byelorussian, Macedonian, Russian, Serbia'
        ,   'cp1252\tWestern Europ'
        ,   'cp1253\tGree'
        ,   'cp1254\tTurkis'
        ,   'cp1255\tHebre'
        ,   'cp1257\tBaltic language'
        ,   'cp65001\tWindows only: Windows UTF-8 (CP_UTF8)'
        ,   'latin_1\tWest Europ'
        ,   'iso8859_2\tCentral and Eastern Europ'
        ,   'iso8859_3\tEsperanto, Maltes'
        ,   'iso8859_4\tBaltic language'
        ,   'iso8859_5\tBulgarian, Byelorussian, Macedonian, Russian, Serbia'
        ,   'iso8859_6\tArabi'
        ,   'iso8859_7\tGree'
        ,   'iso8859_8\tHebre'
        ,   'iso8859_9\tTurkis'
        ,   'iso8859_10\tNordic language'
        ,   'iso8859_13\tBaltic language'
        ,   'iso8859_14\tCeltic language'
        ,   'iso8859_15\tWestern Europ'
        ,   'iso8859_16\tSouth-Eastern Europ'
        ,   'koi8_r\tRussia'
        ,   'koi8_u\tUkrainia'
        ,   'mac_cyrillic\tBulgarian, Byelorussian, Macedonian, Russian, Serbia'
        ,   'mac_greek\tGree'
        ,   'mac_iceland\tIcelandi'
        ,   'mac_latin2\tCentral and Eastern Europ'
        ,   'mac_roman\tWestern Europ'
        ,   'mac_turkish\tTurkis'
        ,   'ptcp154\tKazak'
        ,   'utf_32\tall language'
        ,   'utf_32_be\tall language'
        ,   'utf_32_le\tall language'
        ,   'utf_16\tall language'
        ,   'utf_16_be\tall language'
        ,   'utf_16_le\tall language'
        ,   'utf_7\tall language'
        ,   'utf_8_sig\tall language'
        ]
       #def get_encoding_names
       
    def get_usage_names(self):
        return [
            RSLT_TO_PANEL
        ,   RSLT_TO_PANEL_AP
        ,   RSLT_TO_NEWDOC
        ,   RSLT_TO_CLIP
        ,   RSLT_REPL_SEL
        ]
       #def get_usage_names
   #class Command

def quot(text):
    return '"' + text + '"'
def repr_(text):
    return '"' + text + '"'
#   return 'r"' + text + '"'
'''
ToDo
[ ][kv-kv][09dec15] Run test cmd
'''
