''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
    Alexey Torgashin (CudaText)
Version:
    '1.2.37 2019-05-28'
ToDo: (see end of file)
'''

import  os, json, random, subprocess, shlex, copy, collections, re, zlib, tempfile
import  webbrowser, urllib
import  importlib
import  cudatext            as app
from    cudatext        import ed
import  cudatext_cmd        as cmds
import  cudax_lib           as apx
from    cudax_lib       import log
from    .encodings      import *
from    .cd_plug_lib    import *

pass;                           # Logging
pass;                           from pprint import pformat
pass;                           import inspect
pass;                           LOG = (-2== 2)  # Do or dont logging.
l=chr(13)
OrdDict = collections.OrderedDict

FROM_API_VERSION = '1.0.120' # dlg_custom: type=linklabel, hint
FROM_API_VERSION = '1.0.172' # menu_proc() <== PROC_MENU_*
FROM_API_VERSION = '1.0.182' # LOG_GET_LINES_LIST
FROM_API_VERSION = '1.0.185' # menu_proc() with hotkey, tag
FROM_API_VERSION = '1.0.187' # LEXER_GET_PROP

# I18N
_       = get_translation(__file__)

VERSION     = re.split('Version:', __doc__)[1].split("'")[1]
VERSION_V,  \
VERSION_D   = VERSION.split(' ')

with_proj_man   = False
get_proj_vars   = lambda:{}
try:
    import cuda_project_man
    def get_proj_vars():
        prj_vars = cuda_project_man.project_variables()
        if prj_vars.get('ProjDir', ''):
            # Project loaded
            new_dict = {'{'+s+'}': prj_vars[s] for s in prj_vars}
            #print(new_dict)
            return new_dict
        return {}
    test    = get_proj_vars()
    with_proj_man   = True
except:
    pass;                      #LOG and log('No proj vars',())
    get_proj_vars   = lambda:{}

JSON_FORMAT_VER = '20151209'
EXTS_JSON       = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'exttools.json'

ADV_PROPS       = [ {'key':'source_tab_as_blanks'
                    ,'cap':_('(Int, Default=4) Interpret output symbol TAB as "N spaces".')
                    ,'hnt':_('Set 8 for a tool likes "tidy"')
                    ,'def':'4'
                    }
                 #, {'key':'smth'
                 #  ,'cap':'Smth'
                 #  ,'hnt':'s m t h'
                 #  ,'def':''
                 #  }
                  ]

RSLT_NO         = _('Ignore')
RSLT_TO_PANEL   = _('Output panel')
RSLT_TO_PANEL_AP= _('Output panel, append')
RSLT_TO_CONSOLE = _('Console')
RSLT_TO_NEWDOC  = _('Copy to new document')
RSLT_TO_NEWDOC1 = _('Copy to new document, group 1')
RSLT_TO_NEWDOC2 = _('Copy to new document, group 2')
RSLT_TO_NEWDOC3 = _('Copy to new document, group 3')
RSLT_TO_CLIP    = _('Copy to clipboard')
RSLT_REPL_SEL   = _('Replace selection')
RSLT_N          = 'N'
RSLT_OP         = 'OP'
RSLT_OPA        = 'OPA'
RSLT_CON        = 'CON'
RSLT_ND         = 'ND'
RSLT_ND1        = 'ND1'
RSLT_ND2        = 'ND2'
RSLT_ND3        = 'ND3'
RSLT_CB         = 'CB'
RSLT_SEL        = 'SEL'

SAVS_NOTHING    = _('Nothing')
SAVS_ONLY_CUR   = _('Current document')
SAVS_ALL_DOCS   = _('All documents')
SAVS_N          = 'N'
SAVS_Y          = 'Y'
SAVS_A          = 'A'

#def F(s, *args, **kwargs):return s.format(*args, **kwargs)
#GAP     = 5

def dlg_help_vars():
    EXT_HELP_BODY   = \
_('''In tool properties "File name", "Parameters", "Initial folder"
    the following macros are processed.
• Application:
   {AppDir}           - Directory with app executable
   {AppDrive}         - (Windows) Disk of app executable, eg "C:"
• Currently focused file:
   {FileName}         - Full path
   {FileDir}          - Folder path, without file name
   {FileNameOnly}     - Name only, without folder path
   {FileNameNoExt}    - Name without extension and path
   {FileExt}          - Extension
   {ContentAsTemp}    - Name of [temporary] file with current text
   {Lexer}            - Name of global lexer
• Current file in group N (N is 1...6):
   {FileName_gN}      - Full path
   {FileDir_gN}       - Folder path, without file name
   {FileNameOnly_gN}  - Name only, without folder path
   {FileNameNoExt_gN} - Name without extension and path
   {FileExt_gN}       - Extension
   {ContentAsTemp_gN} - Name of [temporary] file with current text
   {Lexer_gN}         - Name of global lexer
• Currently focused editor (for top caret):
   {CurrentLine}      - Text of caret's line
   {CurrentLineNum}   - Index of caret's line
   {CurrentLineNum0}  - Index of caret's line, 0-based
   {CurrentColumnNum} - Index of caret's column
   {CurrentColumnNum0}- Index of caret's column, 0-based
   {LexerAtCaret}     - Name of lexer at caret position
   {SelectedText}     - Text of selection
   {CurrentWord}      - Word at caret position
• Prompts:
   {Interactive}      - Text will be asked at each running
   {InteractiveFile}  - File name will be asked
• Project:
    {PRJNAME}         - If current project is loaded and has the PRJNAME var
• OS environments:
    {OS:ENVNAME}      - If OS has ENVNAME environment
   
All macros can include suffix (function) to transform value.
   {Lexer|fun}             - gets fun({Lexer})
   {Lexer|fun:p1,p2}       - gets fun({Lexer},p1,p2)
   {Lexer|f1st:p1,p2|f2nd} - gets f2nd(f1st({Lexer},p1,p2))
Predefined functions are:
   q - quote: "AB=?"    -> "AB%3D%3F"
   u - upper: "word"    -> "WORD"
   l - lower: "WORD"    -> "word"
   t - title: "we he"   -> "We He"
All functions from all std Python modules can be used, but not methods.
   q is short form of urllib.parse.quote
''')
    dlg_wrapper(_('Tool macros'), GAP*2+590, GAP*3+25+600,
         [dict(cid='htx',tp='me'    ,t=GAP  ,h=600  ,l=GAP          ,w=590  ,props='1,1,1' ) #  ro,mono,border
         ,dict(cid='-'  ,tp='bt'    ,t=GAP+600+GAP  ,l=GAP+590-90   ,w=90   ,cap='&Close'  )
         ], dict(htx=EXT_HELP_BODY), focus_cid='htx')
   #def dlg_help_vars

DEF_PRESETS = [
        {   "run": "bcc32.exe",
            "re": "\\w+ \\w+ (?P<file>.+) (?P<line>\\d+):.*",
            "name": "Borland C++"
        },
        {   "run": "brcc32.exe",
            "re": "\\w+ (?P<file>.+) (?P<line>\\d+) (?P<col>\\d+): .+",
            "name": "Borland Resource Compiler"
        },
        {   "run": "csslint-wsh.js",
            "re": "(?P<file>.+)\\((?P<line>\\d+),(?P<col>\\d+)\\) .+",
            "name": "CSS Lint"
        },
        {   "run": "dart2js.bat",
            "re": "(?P<file>.+?):(?P<line>\\d+):(?P<col>\\d+): Error:.+",
            "name": "Dart"
        },
        {   "run": "dcc32.exe",
            "re": "^(?P<file>.+)\\((?P<line>\\d+)\\) .*",
            "name": "Delphi"
        },
        {   "run": "gcc*",
            "re": "(?P<file>[^:]+):(?P<line>\d+):(?P<col>\d+): .+",
            "name": "GNU C++"
        },
        {   "run": "iscc.exe",
            "re": ".+ on line (?P<line>\\d+) in (?P<file>.+\\.iss):.+",
            "name": "Inno Setup"
        },
        {   "run": "javac.exe",
            "re": "(?P<file>.+):(?P<line>\\d+): .+",
            "name": "Java"
        },
        {   "run": "jshint.js",
            "re": "Line (?P<file>\\d+) character (?P<line>\\d+):.+",
            "name": "JSHint"
        },
        {   "run": "jsl.exe",
            "re": "(?P<file>.+)\\((?P<line>\\d+)\\): .+",
            "name": "JavaScript Lint"
        },
        {   "run": "ml.exe",
            "re": "(?P<file>.+)\\((?P<line>\\d+)\\).*",
            "name": "MS Macro Assembler"
        },
        {   "run": "msbuild.exe",
            "re": "(?P<file>.+)\\((?P<line>\\d+)\\,(?P<col>\\d+)\\): .*",
            "name": "MSBuild"
        },
        {   "run": "csc.exe",
            "re": "(?P<file>.+)\\((?P<line>\\d+)\\,(?P<col>\\d+)\\): .*",
            "name": "MS C#"
        },
        {   "run": "cl.exe",
            "re": "(?P<file>.+)\\((?P<line>\\d+)\\).*",
            "name": "MS C++"
        },
        {   "run": "makensis.exe",
            "re": ".+ \"(?P<file>.+)\" on line (?P<line>\\d+) .+",
            "name": "NSIS"
        },
        {   "run": "rexxc.exe",
            "re": ".+ running (?P<file>.+) line (?P<line>\\d+):.+",
            "name": "ooRexx"
        },
        {   "run": "perl.exe",
            "re": "^.+ at (?P<file>.+) line (?P<line>\\d+).*",
            "name": "Perl"
        },
        {   "run": "php.exe",
            "re": "^.+ in (?P<file>.+) on line (?P<line>\\d+)",
            "name": "PHP"
        },
        {   "test": "  File \"C:\\work-folder\\work-file.py\", line 123",
            "run": "python.exe",
            "re": "  \\w+ \"(?P<file>.+)\", line (?P<line>\\d+).*",
            "name": "Python"
        },
        {   "run": "ruby.exe",
            "re": "^.+/(?P<file>.+):(?P<line>\\d+):",
            "name": "Ruby"
        },
        {   "run": "tasm32.exe",
            "re": "\\*+\\w+\\*+ (?P<file>.+)\\((?P<line>\\d+)\\).*",
            "name": "Turbo Assembler"
        },
        {   "run": "tsc.exe",
            "re": "(?P<file>.+?)\\s*\\((?P<line>\\d+),(?P<col>\\d+)\\):.+",
            "name": "TypeScript"
        },
        {   "run": "fpc",
            "re": "^(?P<file>[^\(]+)\((?P<line>\d+),(?P<col>\d+)\) .+",
            "name": "FreePascal"
        },
        ]

class Command:
    def __init__(self):
        if app.app_api_version()<FROM_API_VERSION:  return log_status(_('Need update CudaText'))
        # Static data
        self.savs_caps  = [SAVS_NOTHING, SAVS_ONLY_CUR, SAVS_ALL_DOCS]
        self.savs_vals  = [SAVS_N,       SAVS_Y,        SAVS_A]
        self.savs_v2c   = {SAVS_N:SAVS_NOTHING
                          ,SAVS_Y:SAVS_ONLY_CUR
                          ,SAVS_A:SAVS_ALL_DOCS}
        self.rslt_caps  = [RSLT_NO, RSLT_TO_PANEL, RSLT_TO_PANEL_AP, RSLT_TO_CONSOLE, RSLT_TO_NEWDOC, RSLT_TO_NEWDOC1, RSLT_TO_NEWDOC2, RSLT_TO_NEWDOC3, RSLT_TO_CLIP, RSLT_REPL_SEL]
        self.rslt_vals  = [RSLT_N,  RSLT_OP,       RSLT_OPA,         RSLT_CON,        RSLT_ND,        RSLT_ND1,        RSLT_ND2,        RSLT_ND3,        RSLT_CB,      RSLT_SEL]
        self.rslt_v2c   = {RSLT_N:  RSLT_NO
                          ,RSLT_OP: RSLT_TO_PANEL
                          ,RSLT_OPA:RSLT_TO_PANEL_AP
                          ,RSLT_CON:RSLT_TO_CONSOLE
                          ,RSLT_ND: RSLT_TO_NEWDOC
                          ,RSLT_ND1: RSLT_TO_NEWDOC1
                          ,RSLT_ND2: RSLT_TO_NEWDOC2
                          ,RSLT_ND3: RSLT_TO_NEWDOC3
                          ,RSLT_CB: RSLT_TO_CLIP
                          ,RSLT_SEL:RSLT_REPL_SEL}

        # Saving data
        self.saving     = apx._json_loads(open(EXTS_JSON).read()) if os.path.exists(EXTS_JSON) else {
                             'ver':JSON_FORMAT_VER
                            ,'list':[]
                            ,'urls':[]
                            ,'dlg_prs':{}
                            ,'ext4lxr':{}
                            ,'preset':[]
                            ,'umacrs':[]
                            }
        if self.saving.setdefault('ver', '') < JSON_FORMAT_VER:
            # Adapt to new format
            pass
        # Upgrade
        if not self.saving.get('preset'):
            self.saving['preset'] = DEF_PRESETS
        self.dlg_prs    = self.saving.setdefault('dlg_prs', {})
        self.ext4lxr    = self.saving.setdefault('ext4lxr', {})
        self.preset     = self.saving.setdefault('preset', [])
        self.umacrs     = self.saving.setdefault('umacrs', [])
        self.urls       = self.saving.setdefault('urls', [])
        self.exts       = self.saving['list']
            
        # Update
        nms = {m['name'] for m in self.preset}
        for m in DEF_PRESETS:
            if m['name'] not in nms:
                self.preset.append(m)
            
        # Runtime data
        self.last_is_ext= True
        self.url4id     = {str(url['id']):url for url in self.urls}
        self.last_url_id= 0
        self.ext4id     = {str(ext['id']):ext for ext in self.exts}
        self.crcs       = {}
        self.last_crc   = -1
        self.last_ext_id= 0
        self.last_op_ind= -1

        # Adjust
        for ext in self.exts:
            self._fill_ext(ext)

        # Actualize lexer-tool 
        lxrs_l  = app.lexer_proc(app.LEXER_GET_LEXERS, False) + ['(none)']
#       lxrs_l  = _get_lexers()
        for i_lxr in range(len(self.ext4lxr)-1,-1,-1):
            lxr = list(self.ext4lxr.keys())[i_lxr]
            if lxr                    not in lxrs_l \
            or str(self.ext4lxr[lxr]) not in self.ext4id:
                del self.ext4lxr[lxr]
        pass;                  #LOG and log('self.preset={}',self.preset)
       #def __init__
       
    def on_start(self, ed_self):
        if app.app_api_version()<FROM_API_VERSION:  return log_status(_('Need update CudaText'))
        pass
        self._do_acts(acts='|reg|menu|')
       #def on_start
        
    def adapt_menu(self, id_menu=0):
        ''' Add or change top-level menu ExtTools
            Param id_menu points to exist menu item (ie by ConfigMenu) for filling
        '''
        if app.app_api_version()<FROM_API_VERSION:  return log_status(_('Need update CudaText'))
        pass;                  #LOG and log('id_menu={} stack={}',id_menu,inspect.stack())
        PLUG_AUTAG  = 'auto_config:cuda_exttools,adapt_menu'    # tag for ConfigMenu to call this method
        if id_menu!=0:
            # Use this id
            pass;               LOG and log('###Use par id_menu',)
            app.menu_proc(              id_menu, app.MENU_CLEAR)
        else:
            top_its = app.menu_proc(    'top', app.MENU_ENUM)
            pass;              #LOG and log('top_its={}',top_its)
            if PLUG_AUTAG in [it['tag'] for it in top_its]:
                # Reuse id from 'top'
                pass;           LOG and log('Reuse by tag',)
                id_menu = [it['id'] for it in top_its if it['tag']==PLUG_AUTAG][0]
                app.menu_proc(          id_menu, app.MENU_CLEAR)
                pass;          #LOG and log('CLEAR id_menu={}',id_menu)
            else:
                # Create AFTER Plugins
                pass;           LOG and log('Create AFTER Plugin',)
                plg_ind = [ind for ind,it in enumerate(top_its) if 'plugins' in it['hint']][0]
                pass;          #LOG and log('plg_ind={}',plg_ind)
                id_menu = app.menu_proc('top', app.MENU_ADD, tag=PLUG_AUTAG, index=1+plg_ind,       caption=_('&Tools'))
                pass;          #LOG and log('ADD id_menu,plg_ind={}',id_menu,plg_ind)
        pass;                  #LOG and log('id_menu={}',id_menu)
        # Fill
        app.menu_proc(          id_menu, app.MENU_ADD, command=self.dlg_config,                     caption=_('Con&fig...')
                     , hotkey=get_hotkeys_desc(      'cuda_exttools,dlg_config'))
        app.menu_proc(          id_menu, app.MENU_ADD, command=self.run_lxr_main,                   caption=_('R&un main lexer tool')
                     , hotkey=get_hotkeys_desc(      'cuda_exttools,run_lxr_main'))
        id_rslt = app.menu_proc(id_menu, app.MENU_ADD, command='0',                                 caption=_('Resul&ts'))
        app.menu_proc(          id_rslt, app.MENU_ADD, command=self.show_next_result,               caption=    _('&Next tool result')
                     , hotkey=get_hotkeys_desc(      'cuda_exttools,show_next_result'))
        app.menu_proc(          id_rslt, app.MENU_ADD, command=self.show_prev_result,               caption=    _('&Previous tool result')
                     , hotkey=get_hotkeys_desc(      'cuda_exttools,show_prev_result'))
        def call_with(call,p):
            return lambda:call(p)
        if 0<len(self.exts):
            app.menu_proc(      id_menu, app.MENU_ADD,                                              caption='-')
            for ext in self.exts:
                app.menu_proc(  id_menu, app.MENU_ADD, command=call_with(self.run,       ext['id']),caption=ext['nm']
                             , hotkey=get_hotkeys_desc(      f('cuda_exttools,run,{}',   ext['id'])))
        if 0<len(self.urls):
            app.menu_proc(      id_menu, app.MENU_ADD,                                              caption='-')
            for url in self.urls:
                app.menu_proc(  id_menu, app.MENU_ADD, command=call_with(self.browse,    url['id']),caption=url['nm']
                             , hotkey=get_hotkeys_desc(      f('cuda_exttools,browse,{}',url['id'])))
       #def adapt_menu
        
    def _do_acts(self, what='', acts='|save|second|reg|keys|menu|'):
        ''' Use exts list '''
        pass;                  #LOG and log('what, acts={}',(what, acts))
        # Save
        if '|save|' in acts:
            open(EXTS_JSON, 'w').write(json.dumps(self.saving, indent=4))
        
        # Secondary data
        if '|second|' in acts:
            self.ext4id     = {str(ext['id']):ext for ext in self.exts}
            self.url4id     = {str(url['id']):url for url in self.urls}
        
        # Register new subcommands
        if '|reg|' in acts:
            reg_subs        = 'cuda_exttools;run;' + '\n'.join(f('Tools: {}\t{}', ext['nm'], ext['id']) for ext in self.exts)
            pass;              #LOG and log('exts reg_subs={}',reg_subs)
            app.app_proc(app.PROC_SET_SUBCOMMANDS, reg_subs)
            reg_subs        = 'cuda_exttools;browse;' + '\n'.join(f('Urls: {}\t{}', url['nm'], url['id']) for url in self.urls)
            pass;              #LOG and log('urls reg_subs={}',reg_subs)
            app.app_proc(app.PROC_SET_SUBCOMMANDS, reg_subs)
        
        # Clear keys.json
        if '|keys|' in acts and ':' in what:
            # Need delete a key 'cuda_exttools,run,NNNNN'
            itm_id      = what[1+what.index(':'):]
            itm_key     = 'cuda_exttools,run,'+itm_id \
                            if itm_id in self.ext4id else \
                          'cuda_exttools,browse,'+itm_id \
                            if itm_id in self.url4id else \
                          ''
            keys_json   = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'keys.json'
            if not os.path.exists(keys_json): return
            keys        = apx._json_loads(open(keys_json).read())
            pass;              #LOG and log('??? key={}',itm_key)
            if keys.pop(itm_key, None) is not None:
                pass;           LOG and log('UPD keys.json, deleted key={}',itm_key)
                open(keys_json, 'w').write(json.dumps(keys, indent=2))
        
        # [Re]Build menu
        if '|menu|' in acts:
            self.adapt_menu()
       #def _do_acts

    def run_lxr_main(self):
        lxr     = ed.get_prop(app.PROP_LEXER_FILE)
        if lxr not in self.ext4lxr:
            return log_status(f(_('No main lexer tool for "{}"'), lxr))
        self.run(self.ext4lxr[lxr])
       #def run_lxr_main

    def browse(self, url_id):
        ''' Main (and single) way to browse any urltool
        '''
        self.last_is_ext    = False
        self.last_url_id    = url_id
        url_id  = str(url_id)
        pass;                  #LOG and log('url_id={}',url_id)
        url     = self.url4id.get(url_id)
        if url is None:
            return log_status(f(_('No URL: {}'), url_id))
        ref = url['url']

        # Preparing
        file_nm = ed.get_filename()
        if  not file_nm and '{File' in ref:
            return log_status(f(_('Cannot open URL "{}" for untitled tab'), url['nm']))
        (cCrt, rCrt
        ,cEnd, rEnd)    = ed.get_carets()[0]
        umc_vals= self._calc_umc_vals()
        ref = _subst_fltd_props(ref, file_nm, cCrt, rCrt, url['nm'], umcs=umc_vals, prjs=get_proj_vars())
#       ref = _subst_props(ref, file_nm, cCrt, rCrt, url['nm'], umcs=umc_vals, prjs=get_proj_vars())

        app.msg_status(f(_('Opened "{}": {}'), url['nm'], ref))
#       webbrowser.open_new_tab(ref)
        pass;                  #LOG and log('quote(ref)={}',(urllib.parse.quote(ref, safe='/:')))
        webbrowser.open_new_tab(urllib.parse.quote(ref, safe='/:#?='))
        return True
       #def browse
    
#   def run(self, ext_id):
    def run(self, info=None):
        ''' Main (and single) way to run any exttool
        '''
        ext_id  = info                  # For call as "module=cuda_exttools;cmd=run;info=id"
        self.last_is_ext    = True
        self.last_ext_id    = ext_id
        ext_id  = str(ext_id)
        pass;                  #LOG and log('ext_id={}',ext_id)
        ext     = self.ext4id.get(ext_id)
        if ext is None:
            return log_status(_('No tool: {}').format(ext_id))
        nm      = ext['nm']
        lxrs    = ext['lxrs']
        lxr_cur = ed.get_prop(app.PROP_LEXER_FILE)
        lxr_cur = lxr_cur if lxr_cur else '(none)' 
        pass;                  #LOG and log('nm="{}", lxr_cur="{}", lxrs="{}"',nm, lxr_cur, lxrs)
        if (lxrs
        and not (','+lxr_cur+',' in ','+lxrs+',')):
            return log_status(_('Tool "{}" is only for lexer(s): {}').format(nm, lxrs))
#           return app.msg_status(_('Tool "{}" is not suitable for lexer "{}". It works only with "{}"').format(nm, lxr_cur, lxrs))

        jext    = ext.get('jext')
        if jext:
            for subid in jext:
                if not self.run(subid):
                    return False
            return True
        
        cmnd    = ext['file']
        prms_s  = ext['prms']
        ddir    = ext['ddir']
        ddir    = ddir if ddir else '{FileDir}'     # Default InitDir set to {FileDir}
        pass;                  #LOG and log('nm="{}", cmnd="{}", ddir="{}", prms_s="{}"',nm, cmnd, ddir, prms_s)
        
        # Saving
        if SAVS_Y==ext.get('savs', SAVS_N):
            if not ed.save():       return app.msg_status(_('Cancel running tool "{}"'.format(nm)))
#           if not app.file_save(): return app.msg_status(_('Cancel running tool "{}"'.format(nm)))
        if SAVS_A==ext.get('savs', SAVS_N):
            ed.cmd(cmds.cmd_FileSaveAll)
            for h in app.ed_handles():
                if app.Editor(h).get_prop(app.PROP_MODIFIED):
                    return app.msg_status(_('Cancel running tool "{}"'.format(nm)))
        
        # Preparing
        file_nm = ed.get_filename()
        if  not file_nm and (
            '{File' in cmnd
        or  '{File' in prms_s
        or  '{File' in ddir ):  return log_status(_('Cannot run tool "{}" for untitled tab'.format(nm)))
        (cCrt, rCrt
        ,cEnd, rEnd)    = ed.get_carets()[0]
        umc_vals= self._calc_umc_vals()
        prms_l  = shlex.split(prms_s)
        for ind, prm in enumerate(prms_l):
            prm_raw = prm
            prm     = _subst_fltd_props(prm,  file_nm, cCrt, rCrt, ext['nm'], umcs=umc_vals, prjs=get_proj_vars())
#           prm     = _subst_props(prm,  file_nm, cCrt, rCrt, ext['nm'], umcs=umc_vals, prjs=get_proj_vars())
            if prm_raw != prm:
                prms_l[ind] = prm
#               prms_l[ind] = shlex.quote(prm)
           #for ind, prm
        cmnd        = _subst_fltd_props(cmnd, file_nm, cCrt, rCrt, ext['nm'], umcs=umc_vals, prjs=get_proj_vars())
#       cmnd        = _subst_props(cmnd, file_nm, cCrt, rCrt, ext['nm'], umcs=umc_vals, prjs=get_proj_vars())
        ddir        = _subst_fltd_props(ddir, file_nm, cCrt, rCrt, ext['nm'], umcs=umc_vals, prjs=get_proj_vars())
#       ddir        = _subst_props(ddir, file_nm, cCrt, rCrt, ext['nm'], umcs=umc_vals, prjs=get_proj_vars())

        pass;                  #LOG and log('ready prms_l={}',(prms_l))

        val4call= [cmnd] + prms_l
        pass;                  #LOG and log('val4call={}',(val4call))

        # Calling
        rslt    = ext.get('rslt', RSLT_N)
        nmargs  = {'cwd':ddir} if ddir else {}
        if RSLT_N==rslt:
            # Without capture
            try:
                app.msg_status(_('Run: "{}"'.format(nm)))
                subprocess.Popen(val4call, **nmargs)
            except Exception as ex:
                app.msg_box('{}: {}'.format(type(ex).__name__, ex), app.MB_ICONWARNING)
                pass;           LOG and log('fail Popen',)
                return False
            return True
        
        # With capture
        pass;                  #LOG and log("'Y'==ext.get('shll', 'N')",'Y'==ext.get('shll', 'N'))
        nmargs['stdout']=subprocess.PIPE
        nmargs['stderr']=subprocess.STDOUT
        nmargs['shell'] =ext.get('shll', False)
        pass;                  #LOG and log('?? Popen nmargs={}',nmargs)
        try:
            app.msg_status(_('Run: "{}"'.format(nm)))
            pipe    = subprocess.Popen(val4call, **nmargs)
        except Exception as ex:
            app.msg_box('{}: {}'.format(type(ex).__name__, ex), app.MB_ICONWARNING)
            pass;               LOG and log('fail Popen',)
            return False
        if pipe is None:
            pass;               LOG and log('fail Popen',)
            app.msg_status(_('Fail running: {} {}').format(cmnd, prms_s))
            return False
        pass;                  #LOG and log('ok Popen',)
        app.msg_status(_('Run: {} {}').format(cmnd, prms_s))

        rslt_txt= ''
        crc_tag = 0
        def gen_save_crc(ext, cwd='', filepath='', filecol=0, filerow=0):
            ''' Generate 32-bit int for each ext running '''
            text    = '|'.join([str(ext[k]) for k in ext]
                              +[f('{}|{}|{}|{}|{}', cwd, filepath, cCrt, rCrt, len(self.crcs))]
                              )
            crc     = zlib.crc32(text.encode()) & 0x0fffffff
            self.last_crc   = crc
            self.crcs[crc]  = {  'ext':ext
                                ,'cwd':cwd
                                ,'pth':filepath
                                ,'col':cCrt
                                ,'row':rCrt
                                }
            return crc
        if False:pass
        elif rslt in (RSLT_OP, RSLT_OPA):
            crc_tag = gen_save_crc(ext, os.path.abspath('.'), file_nm, cCrt, rCrt)
            self.last_op_ind = -1
            ed.cmd(cmds.cmd_ShowPanelOutput)
            ed.focus()
            if rslt==RSLT_OP:
                app.app_log(app.LOG_CLEAR, '', panel=app.LOG_PANEL_OUTPUT)
#               self.last_op_ind = -1
            else: # rslt==RSLT_OPA
                pass
        elif rslt == RSLT_CON:
            ed.cmd(cmds.cmd_ShowPanelConsole)
            print('--- Output of external tool ---')
        elif rslt ==  RSLT_ND:
            app.file_open('')
        elif rslt == RSLT_ND1:
            app.file_open('', group=0)
        elif rslt == RSLT_ND2:
            if app.app_proc(app.PROC_GET_GROUPING, '') == app.GROUPS_ONE:
                app.app_proc(app.PROC_SET_GROUPING, app.GROUPS_2VERT)
            app.file_open('', group=1)
        elif rslt == RSLT_ND3:
            if app.app_proc(app.PROC_GET_GROUPING, '') in (app.GROUPS_ONE, app.GROUPS_2HORZ, app.GROUPS_2VERT):
                app.app_proc(app.PROC_SET_GROUPING, app.GROUPS_3VERT)
            app.file_open('', group=2)

        while True:
            # 'encd' can be empty string, fixed here
            out_ln = pipe.stdout.readline().decode(ext.get('encd') or 'utf_8')
            if 0==len(out_ln): break
            out_ln = out_ln.strip('\r\n')
            pass;              #LOG and log('out_ln={}',out_ln)
            if False:pass
            elif rslt in (RSLT_OP, RSLT_OPA):
                app.app_log(app.LOG_ADD, out_ln, crc_tag, panel=app.LOG_PANEL_OUTPUT)
            elif rslt == RSLT_CON:
                print(out_ln)
            elif rslt in (RSLT_ND, RSLT_ND1, RSLT_ND2, RSLT_ND3):
                ed.set_text_line(-1, out_ln)
            elif rslt in (RSLT_CB, RSLT_SEL):
                rslt_txt+= out_ln + '\n'
           #while True

#       rslt_txt= rslt_txt.strip('\n')
        if False:pass
        elif rslt == RSLT_CB:
            app.app_proc(app.PROC_SET_CLIP, rslt_txt)
        elif rslt == RSLT_SEL:
            crts    = ed.get_carets()
            crts.reverse()
            for (cCrt, rCrt, cEnd, rEnd) in crts:
                stripped    = False
                if -1!=cEnd:
                    (rCrt, cCrt), (rEnd, cEnd) = apx.minmax((rCrt, cCrt), (rEnd, cEnd))
                    stripped= not(cEnd==0                           # Sel ends with EOL (at start of last line)
                              or  cEnd==len(ed.get_text_line(rEnd)) # Sel ends before EOL/EOF
                                )
                    ed.delete(cCrt, rCrt, cEnd, rEnd)
                else:
                    stripped= not(cCrt==0                           # Caret at start of line
                              or  cCrt==len(ed.get_text_line(rCrt)) # Caret before EOL/EOF
                                )
                ed.insert(cCrt, rCrt
                         ,rslt_txt.strip('\n') if stripped else rslt_txt)
        elif rslt in (RSLT_OP, RSLT_OPA):
            ed.focus()
            
        return True
       #def run
       
    def on_output_nav(self, ed_self, output_line, crc_tag):
        pass;                  #LOG and log('output_line, crc_tag={}',(output_line, crc_tag))
        
        crc_inf = self.crcs.get(crc_tag, {})
        ext     = crc_inf.get('ext')
        if not ext:                         app.msg_status(_('No tool to parse the output line'));return
        if not ext['pttn']:                 app.msg_status(_('Tool "{}" has not Pattern property').format(ext['nm']));return
        pttn    = ext['pttn']
        grp_dic = re.search(pttn, output_line).groupdict('') if re.search(pttn, output_line) is not None else {}
        if not grp_dic or not (
            'line'  in grp_dic 
        or  'line0' in grp_dic):            app.msg_status(_('Tool "{}" could not find a line-number into output line').format(ext['nm']));return # '
        nav_file=     grp_dic.get('file' , crc_inf['pth']  )
        nav_line= int(grp_dic.get('line' , 1+int(grp_dic.get('line0', 0))))-1
        nav_col = int(grp_dic.get('col'  , 1+int(grp_dic.get('col0' , 0))))-1
        pass;                  #LOG and log('nav_file, nav_line, nav_col={}',(nav_file, nav_line, nav_col))
        bs_dir  = ext['ddir']
        bs_dir  = bs_dir if bs_dir else '{FileDir}'
        bs_dir  = os.path.dirname(crc_inf['pth']) \
                    if not bs_dir else  \
                  _subst_fltd_props(bs_dir, crc_inf['pth'], umcs=self._calc_umc_vals(), prjs=get_proj_vars())
#                 _subst_props(bs_dir, crc_inf['pth'], umcs=self._calc_umc_vals(), prjs=get_proj_vars())
        nav_file= os.path.join(bs_dir, nav_file)
        pass;                  #LOG and log('nav_file={}',(nav_file))
        if not os.path.exists(nav_file):    app.msg_status(_('Cannot open: {}').format(nav_file));return
        
        self.last_op_ind = app.app_log(app. LOG_GET_LINEINDEX, '', panel=app.LOG_PANEL_OUTPUT)
        
        nav_ed  = _file_open(nav_file)
        if nav_ed is None:                  app.msg_status(_('Cannot open: {}').format(nav_file));return
        nav_ed.focus()
        if 'source_tab_as_blanks' in ext:
            # ReCount nav_col for the tab_size
            tool_tab_sz = int(ext['source_tab_as_blanks'])
            ed_tab_sz   = apx.get_opt('tab_size', lev=apx.CONFIG_LEV_FILE)
            pass;              #LOG and log('nav_col, nav_line, tool_tab_sz, ed_tab_sz={}',(nav_col, nav_line, tool_tab_sz, ed_tab_sz))
            if tool_tab_sz != ed_tab_sz:
                ed.lock()
                apx.set_opt('tab_size', str(tool_tab_sz), lev=apx.CONFIG_LEV_FILE)
            nav_col = ed.convert(app.CONVERT_COL_TO_CHAR, nav_col, nav_line)[0]
            pass;              #LOG and log('nav_col={}',(nav_col))
            if tool_tab_sz != ed_tab_sz:
                apx.set_opt('tab_size', str(ed_tab_sz),   lev=apx.CONFIG_LEV_FILE)
                ed.unlock()
        nav_ed.set_caret(nav_col, nav_line)
       #def on_output_nav
       
    def show_next_result(self): self._show_result('next')
    def show_prev_result(self): self._show_result('prev')
    def _show_result(self, what):
        pass;                  #LOG and log('what, last_crc, self.last_op_ind={}',(what, self.last_crc, self.last_op_ind))
        if self.last_crc==-1:
            return app.msg_status(_('No any results for navigation'))

        crc_inf     = self.crcs.get(self.last_crc, {})
        ext         = crc_inf.get('ext')
        ext_pttn    = ext['pttn']
        op_line_tags=app.app_log(app.LOG_GET_LINES_LIST, '', panel=app.LOG_PANEL_OUTPUT)
        pass;                  #LOG and log('op_line_tags={}',op_line_tags)
#       op_line_tags=app.app_log(app.LOG_GET_LINES, '', panel=app.LOG_PANEL_OUTPUT)
#       pass;                   LOG and log('op_line_tags={}',op_line_tags)
#       op_line_tags=[(item.split(c13)[0], int(item.split(c13)[1])) 
#                       if c13 in item else 
#                     (item, 0)
#                       for item in op_line_tags.split(c10)]
#       pass;                   LOG and log('op_line_tags={}',op_line_tags)
        for op_ind in (range(self.last_op_ind+1, len(op_line_tags)) 
                        if what=='next' else
                       range(self.last_op_ind-1, -1, -1) 
                      ):
            line, crc   = op_line_tags[op_ind]
            if crc != self.last_crc:            continue    #for
            if not re.search(ext_pttn, line):   continue    #for
            self.last_op_ind = op_ind
            app.app_log(app. LOG_SET_LINEINDEX, str(op_ind), panel=app.LOG_PANEL_OUTPUT)
            self.on_output_nav(ed, line, crc)
            break   #for
        else:#for
            app.msg_status(_('No more results for navigation'))
       #def _show_result
       
#   def dlg_export(self)
#               lxrs    = ','+ed_ext['lxrs']+','
#               lxrs_l  = _get_lexers()
#               sels    = ['1' if ','+lxr+',' in lxrs else '0' for lxr in lxrs_l]
#               crt     = str(sels.index('1') if '1' in sels else 0)
#
#               lx_cnts =[dict(cid='lxs',tp='ch-lbx',t=GAP,h=400    ,l=GAP          ,w=200  ,items=lxrs_l           ) #
#                        ,dict(cid='!'  ,tp='bt'    ,t=GAP+400+GAP  ,l=    200-140  ,w=70   ,cap=_('OK'),props='1'  ) #  default
#                        ,dict(cid='-'  ,tp='bt'    ,t=GAP+400+GAP  ,l=GAP+200- 70  ,w=70   ,cap=_('Cancel')        ) #  
#                       ]
#               lx_vals = dict(lxs=(crt,sels))
#               lx_btn, \
#               lx_vals,\
#               *_t     = dlg_wrapper(_('Select lexers'), GAP+200+GAP, GAP+400+GAP+24+GAP, lx_cnts, lx_vals, focus_cid='lxs')
##               lx_fid, \
##               lx_chds = dlg_wrapper(_('Select lexers'), GAP+200+GAP, GAP+400+GAP+24+GAP, lx_cnts, lx_vals, focus_cid='lxs')
#               if lx_btn=='!':
#                   crt,sels= lx_vals['lxs']
#                   lxrs    = [lxr for (ind,lxr) in enumerate(lxrs_l) if sels[ind]=='1']
#                   ed_ext['lxrs'] = ','.join(lxrs)
#      #def dlg_export
            
    def dlg_config(self):
        if app.app_api_version()<FROM_API_VERSION:  return log_status(_('Need update CudaText'))

        keys_json   = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'keys.json'
        
        ext_ids = [ext['id'] for ext in self.exts]
        ext_ind = ext_ids.index(self.last_ext_id) if self.last_ext_id in ext_ids else min(0, len(ext_ids)-1)
        url_ids = [url['id'] for url in self.urls]
        url_ind = url_ids.index(self.last_url_id) if self.last_url_id in url_ids else min(0, len(url_ids)-1)

        DTLS_JOIN_H     = _('Join several tools to single tool')
        DTLS_CALL_H     = _('Use the URL')
        DTLS_MVUP_H     = _('Move current tool to upper position')
        DTLS_MVDN_H     = _('Move current tool to lower position')
        DTLS_MNLX_H     = _('For call by command "Run main lexer tool"')
        DTLS_USMS_H     = _("Edit list of user's macros to use in tool properties")
#       DTLS_EXPT_H     = _("Select tools/urls to export its to portable form")
        DTLS_CUST_H     = _('Change this dialog sizes'
                            '\rCtrl+Click - Restore default values')

        GAP2    = GAP*2    
        prs     = self.dlg_prs
        pass;                  #LOG and log('prs={}',prs)
        vals    = dict(lst=ext_ind if self.last_is_ext else url_ind
                      ,tls=           self.last_is_ext
                      ,urs=       not self.last_is_ext
                      ,evl=False)
        while True:
            keys        = apx._json_loads(open(keys_json).read()) if os.path.exists(keys_json) else {}
            ext_nz_d    = OrdDict([
                           (_('Name')           ,prs.get('nm'  , '150'))
                          ,(_('Hotkey')         ,prs.get('keys', '100'))
                          ,(_('File | [Tools]') ,prs.get('file', '180'))
                          ,(_('Params')         ,prs.get('prms', '100'))
                          ,(_('Folder')         ,prs.get('ddir', '100'))
                          ,(_('Lexers')         ,prs.get('lxrs', 'C50'))
                          ,(_('Capture')        ,prs.get('rslt', 'C50'))
                          ,(_('Saving')         ,prs.get('savs', 'C30'))
                          ])
            url_nz_d    = OrdDict([
                           (_('Name')           ,prs.get('nm'  , '150'))
                          ,(_('Hotkey')         ,prs.get('keys', '100'))
                          ,(_('URL')            ,prs.get('url',  '500'))
                          ])
            head_nz_d   = ext_nz_d if vals['tls'] else url_nz_d
            
            ACTS_W          = prs.get('w_btn', 90)
            AW2             = int(ACTS_W/2)
            HT_LST          = prs.get('h_list', 300)
            ACTS_T          = [GAP2+HT_LST  +         25    *(ind-1) for ind in range(20)]
            ACTS_L          = [             + GAP*ind+ACTS_W*(ind-1) for ind in range(20)]

            WD_LST_MIN      = GAP*10+ACTS_W*8
            ext_WD_LST      = sum([int(w.lstrip('LRC')) for w in ext_nz_d.values() if w[0]!='-'])+len(ext_nz_d)+10
            url_WD_LST      = sum([int(w.lstrip('LRC')) for w in url_nz_d.values() if w[0]!='-'])+len(url_nz_d)+10
            if ext_WD_LST < WD_LST_MIN:
                pass;          #LOG and log('ext_WD_LST < WD_LST_MIN={}',(ext_WD_LST, WD_LST_MIN))
                ext_nz_d[_('Name')] = str(WD_LST_MIN - ext_WD_LST + int(ext_nz_d[_('Name')]))
                ext_WD_LST          = WD_LST_MIN
            if url_WD_LST < WD_LST_MIN:
                pass;          #LOG and log('url_WD_LST < WD_LST_MIN={}',(url_WD_LST, WD_LST_MIN))
                url_nz_d[_('Name')] = str(WD_LST_MIN - url_WD_LST + int(url_nz_d[_('Name')]))
                url_WD_LST          = WD_LST_MIN
            if ext_WD_LST < url_WD_LST:
                pass;          #LOG and log('ext_WD_LST < url_WD_LST={}',(ext_WD_LST, url_WD_LST))
                ext_nz_d[_('File | [Tools]')]   = str(url_WD_LST - ext_WD_LST + int(ext_nz_d[_('File | [Tools]')]))
                ext_WD_LST = url_WD_LST
            if url_WD_LST < ext_WD_LST:
                pass;          #LOG and log('url_WD_LST < ext_WD_LST={}',(url_WD_LST, ext_WD_LST))
                url_nz_d[_('URL')]              = str(ext_WD_LST - url_WD_LST + int(url_nz_d[_('URL')]))
                url_WD_LST = ext_WD_LST
            WD_LST = ext_WD_LST
            DLG_W, DLG_H    = max(WD_LST, ACTS_L[9])+GAP*3, ACTS_T[3]+3#+GAP
            pass;              #LOG and log('DLG_W, DLG_H={}',(DLG_W, DLG_H))

            if vals['evl']:
                file_nm = ed.get_filename()
                (cCrt, rCrt
                ,cEnd, rEnd)    = ed.get_carets()[0]
                umc_vals= self._calc_umc_vals()

            ext_vlss    = []
            for ext in (self.exts if vals['tls'] else []):
                jext    = ext.get('jext')
                jids    = jext if jext else [ext['id']]
                jexs    = [ex for ex in self.exts if ex['id'] in jids]
                ext_file= ext.get('file', '')
                ext_prms= ext.get('prms', '')
                ext_ddir= ext.get('ddir', '')
                if vals['evl']:
                    ext_file    = _subst_fltd_props(ext_file, file_nm, cCrt, rCrt, ext['nm'], umcs=umc_vals, prjs=get_proj_vars())
                    ext_prms    = _subst_fltd_props(ext_prms, file_nm, cCrt, rCrt, ext['nm'], umcs=umc_vals, prjs=get_proj_vars())
                    ext_ddir    = _subst_fltd_props(ext_ddir, file_nm, cCrt, rCrt, ext['nm'], umcs=umc_vals, prjs=get_proj_vars())
                ext_vlss+=[[                                    ext['nm']
                          ,get_keys_desc('cuda_exttools,run',   ext['id'], keys)
                          ,(('>' if                             ext['shll'] else '')
                          +                                     ext_file)           if not jext else ' ['+', '.join(ex['nm'] for ex in jexs)+']'
                          ,                                     ext_prms            if not jext else ''
                          ,                                     ext_ddir            if not jext else ''
                          ,                                     ext['lxrs']
                          ,                                     ext['rslt']         if not jext else ''
                          ,                                     ext['savs']
                          ]]
            url_vlss    = []
            for url in ([] if vals['tls'] else self.urls):
                url_url = url['url']
                if vals['evl']:
                    url_url    = _subst_fltd_props(url_url, file_nm, cCrt, rCrt, url['nm'], umcs=umc_vals, prjs=get_proj_vars())
                url_vlss+=[[                                    url['nm']
                          ,get_keys_desc('cuda_exttools,browse',url['id'], keys)
                          ,                                     url_url
                          ]]
            pass;              #LOG and log('ext_vlss={}',ext_vlss)
            pass;              #LOG and log('url_vlss={}',url_vlss)

            ext_ids = [ext['id'] for ext in self.exts]
#           url_ids = [url['id'] for url in self.urls]
            
            vlss    = ext_vlss if vals['tls'] else url_vlss
            itms    = ([(nm, '0' if sz[0]=='-' else sz) for (nm,sz) in head_nz_d.items()], vlss)
#           itms    = ([(nm, '0' if sz[0]=='-' else sz) for (nm,sz) in ext_nz_d.items()], vlss)
            lG0     = 0<len(vlss)
            lG1     = 1<len(vlss)
            #NOTE: list cnts
            cnts    =([]
                    +[dict(cid='tls',tp='ch-bt' ,t=2        ,l=GAP          ,w=120              ,cap=f(_('&Tools ({})'),len(self.exts)) ,act='1')] # &t
                    +[dict(cid='urs',tp='ch-bt' ,t=2        ,l=GAP+120      ,w=120              ,cap=f(_('&URLs ({})' ),len(self.urls)) ,act='1')] # &u
                    +[dict(cid='evl',tp='ch'    ,tid='tls'  ,l=GAP+250      ,w=ACTS_W           ,cap=_('Expanded mac&ros')              ,act='1')] # &r

                    +[dict(cid='lst',tp='lvw'   ,t=GAP+20   ,l=GAP          ,w=4+WD_LST, h=HT_LST-20  ,items=itms                               )] #

                    +[dict(cid='edt',tp='bt'    ,t=ACTS_T[1],l=ACTS_L[1]    ,w=ACTS_W           ,cap=_('&Edit...')          ,props='1'  ,en=lG0 )] # &e  default
                    +[dict(cid='add',tp='bt'    ,t=ACTS_T[1],l=ACTS_L[2]    ,w=ACTS_W           ,cap=_('&Add...')                               )] # &a
                    +[dict(cid='del',tp='bt'    ,t=ACTS_T[2],l=ACTS_L[1]    ,w=ACTS_W           ,cap=_('&Delete...')                    ,en=lG0 )] # &d
                    +[dict(cid='cln',tp='bt'    ,t=ACTS_T[2],l=ACTS_L[2]    ,w=ACTS_W           ,cap=_('Clo&ne...')                     ,en=lG0 )] # &n
                    +([]                                       
                    +[dict(cid='jin',tp='bt'    ,t=ACTS_T[1],l=ACTS_L[3]    ,w=ACTS_W           ,cap=_('Jo&in...')  ,hint=DTLS_JOIN_H   ,en=lG1 )] # &i
                    if vals['tls'] else []
                    +[dict(cid='cll',tp='bt'    ,t=ACTS_T[1],l=ACTS_L[3]    ,w=ACTS_W           ,cap=_('&Call')     ,hint=DTLS_CALL_H   ,en=lG0 )] # &o
                    )
                    +[dict(cid='key',tp='bt'    ,t=ACTS_T[2],l=ACTS_L[3]    ,w=ACTS_W           ,cap=_('Hotke&y...')                    ,en=lG0 )] # &n
                    +[dict(cid='up' ,tp='bt'    ,t=ACTS_T[1],l=ACTS_L[5]-AW2,w=ACTS_W           ,cap=_('U&p')       ,hint=DTLS_MVUP_H   ,en=lG1 )] # &p
                    +[dict(cid='dn' ,tp='bt'    ,t=ACTS_T[2],l=ACTS_L[5]-AW2,w=ACTS_W           ,cap=_('Do&wn')     ,hint=DTLS_MVDN_H   ,en=lG1 )] # &w
                    +([]                                       
                    +[dict(cid='man',tp='bt'    ,t=ACTS_T[1],l=ACTS_L[6]    ,r=ACTS_L[7]+ACTS_W ,cap=_('Set &main for lexers...')
                                                                                                                    ,hint=DTLS_MNLX_H   ,en=lG0 )] # &m
                    if vals['tls'] else [])
                    +[dict(cid='mcr',tp='bt'    ,t=ACTS_T[2],l=ACTS_L[6]    ,r=ACTS_L[7]+ACTS_W ,cap=_('User macro &vars...')
                                                                                                                    ,hint=DTLS_USMS_H           )] # &v
            
#                   +[dict(cid='exp',tp='bt'    ,t=ACTS_T[1],l=ACTS_L[9]-AW2,w=ACTS_W           ,cap=_('E&xport...'),hint=DTLS_EXPT_H           )] # &x
                    
                    +[dict(cid='adj',tp='bt'    ,t=ACTS_T[1],l=DLG_W-GAP-ACTS_W,w=ACTS_W        ,cap=_('Ad&just...'),hint=DTLS_CUST_H           )] # &j
                    +[dict(cid='-'  ,tp='bt'    ,t=ACTS_T[2],l=DLG_W-GAP-ACTS_W,w=ACTS_W        ,cap=_('Close')                                 )] #
                    )

            btn, vals, *_t  = dlg_wrapper(f(_('Tools and URLs ({})'), VERSION_V), DLG_W, DLG_H, cnts, vals, focus_cid='lst')
#           btn, vals, fid, chds = dlg_wrapper(_('Tools and URLs'), DLG_W, DLG_H, cnts, vals, focus_cid='lst')
            if btn is None or btn=='-':  return
            scam            = app.app_proc(app.PROC_GET_KEYSTATE, '') if app.app_api_version()>='1.0.143' else ''
            btn_m           = scam + '/' + btn if scam and scam!='a' else btn   # smth == a/smth
            
            lst_ind = vals['lst']
            ext_ind = lst_ind if     self.last_is_ext else ext_ind
            url_ind = lst_ind if not self.last_is_ext else url_ind
            # Switch lists
            if btn=='tls':  
                self.last_is_ext= True
                vals['tls'] = True; vals['urs'] = False
                vals['lst'] = ext_ind
                vals['evl'] = False
                continue#while
            if btn=='urs':  
                self.last_is_ext= False
                vals['tls'] = False;vals['urs'] = True
                vals['lst'] = url_ind
                vals['evl'] = False
                continue#while

            # Actions not for tool/url
            if btn_m=='c/adj':
                dlg_valign_consts()
                continue#while_fif
#           if btn_m=='c/adj':              # [Ctrl+]Adjust  = restore defs
#               if app.ID_OK == app.msg_box(_('Restore default layout?'), app.MB_OKCANCEL):
#                   self.dlg_prs.clear()
#                   open(EXTS_JSON, 'w').write(json.dumps(self.saving, indent=4))
#               continue#while
            if btn=='adj':                  #Custom dlg controls
                self._dlg_adj_list()
                continue#while

            if btn=='mcr':                  #User macros
                self._dlg_usr_mcrs()
                continue #while
            
            if btn=='man':                  #Main lexer tool
                self._dlg_main_tool(0 if ext_ind==-1 else ext_ids[ext_ind])
                continue #while
            
            self_cllc   = self.exts if vals['tls'] else self.urls
            if False:pass 
            elif btn=='key':                # Assign/Clear hotkey
                app.dlg_hotkeys(f('cuda_exttools,{},{}' 
                                ,'run' if vals['tls'] else 'browse'
                                ,self_cllc[lst_ind]['id']))
                keys    = apx._json_loads(open(keys_json).read()) if os.path.exists(keys_json) else {}
                continue
            
            elif btn=='cll':                # Call URL
                self.browse(self.urls[lst_ind]['id'])
                continue
                
            elif btn=='jin':                # Create joined tool
                jo_ids  = self._dlg_exts_for_join()
                if jo_ids is None or len(jo_ids)<2:
                    continue #while
                ext     = self._fill_ext({'id':_gen_id(self.ext4id)
                                         ,'nm':'tool{}'.format(len(self.exts))
                                         ,'jext':jo_ids
                                        })
                ed_ans      = self._dlg_ext_prop(ext, keys)
                if ed_ans is None:
                    continue #while
                self.exts  += [ext]
                vals['lst'] = len(self.exts)-1
                
            if btn in ('add', 'cln') and vals['urs']:  #Create/Clone URL
                if btn=='add':
                    url     = {'id':_gen_id(self.url4id)
                              ,'nm':f('url{}', 1+len(self.urls))
                              ,'url':''
                              }
                else:
                    url     = copy.deepcopy(self.urls[lst_ind])
                    url['id']= _gen_id(self.url4id)
                    url['nm']= url['nm']+' copy'
                ed_ans      = self._dlg_url_prop(url, keys)
                pass;          #LOG and log('fin edit={}',ed_ans)
                if ed_ans is None:
                    continue #while
                self.urls  += [url]
                vals['lst'] = len(self.urls)-1

            if btn in ('add', 'cln') and vals['tls']:  #Create/Clone Tool
                if btn=='add':
                    pttn4run    = {ps['run']:ps['re']           for ps in self.preset}
                    test4run    = {ps['run']:ps.get('test', '') for ps in self.preset}
                    file4run    = app.dlg_file(True, '!', '', '')   # '!' to disable check "filename exists"
                    file4run    = file4run if file4run is not None else ''
                    id4ext      = _gen_id(self.ext4id)
                    run_nm      = os.path.basename(file4run)
                    ext         = self._fill_ext({'id':id4ext
                                        ,'nm':(run_nm if file4run else f('tool{}', 1+len(self.exts)))
                                        ,'file':file4run
                                        ,'ddir':'{FileDir}'
#                                       ,'ddir':os.path.dirname(file4run)
                                        })
                    if run_nm in pttn4run:
                        ext['pttn']     = pttn4run.get(run_nm, '')
                        ext['pttn-test']= test4run.get(run_nm, '')
                else:
                    ext     = copy.deepcopy(self.exts[lst_ind])
                    ext['id']= _gen_id(self.url4id)
                    ext['nm']= ext['nm']+' copy'
                ed_ans      = self._dlg_ext_prop(ext, keys)
                pass;          #LOG and log('fin edit={}',ed_ans)
                if ed_ans is None:
                    continue #while
                self.exts  += [ext]
                vals['lst'] = len(self.exts)-1

            lst_ind = vals['lst']
            if lst_ind==-1:
                continue #while
                
            what    = ''
            ext_ids     = [ext['id'] for ext in self.exts]
            url_ids     = [url['id'] for url in self.urls]
            if vals['tls']:
                self.last_ext_id    = ext_ids[ext_ind]
            if vals['urs']:
                self.last_url_id    = url_ids[url_ind]
            
#           self_cllc   = self.exts if vals['tls'] else self.urls
            if False:pass
            
            elif btn=='edt' and vals['tls']:#Edit Tool
                ed_ans  = self._dlg_ext_prop(self.exts[ext_ind], keys)
                if ed_ans is None or not ed_ans:
                    continue # while
            elif btn=='edt' and vals['urs']:#Edit URL
                ed_ans  = self._dlg_url_prop(self.urls[url_ind], keys)  ##??
                if ed_ans is None or not ed_ans:
                    continue # while

            elif btn=='up' and lst_ind>0:                   #Up
                (self_cllc[lst_ind-1]
                ,self_cllc[lst_ind  ])  = (self_cllc[lst_ind  ]
                                          ,self_cllc[lst_ind-1])
                vals['lst'] = lst_ind-1
            elif btn=='dn' and lst_ind<(len(self_cllc)-1):  #Down
                (self_cllc[lst_ind  ]
                ,self_cllc[lst_ind+1])  = (self_cllc[lst_ind+1]
                                          ,self_cllc[lst_ind  ])
                vals['lst'] = lst_ind+1
            
            elif btn=='del' and vals['urs']:# Delete URL
                if app.msg_box( _('Delete URL?\n')
                                 +'\n'+self.urls[url_ind]['nm']
                                 +'\n'+self.urls[url_ind]['url']
                              , app.MB_YESNO+app.MB_ICONQUESTION)!=app.ID_YES:
                    continue # while
                id4del      = self.urls[url_ind]['id']
                del self.urls[url_ind]
                vals['lst'] = min(url_ind, len(self.urls)-1)
                what        = 'delete:'+str(id4del)

            elif btn=='del' and vals['tls']:# Delete Tool
#               if app.msg_box( 'Delete Tool\n    {}'.format(exkys[ext_ind])
                flds    = list(head_nz_d.keys())
#               flds    = list(ext_nz_d.keys())
                ext_vls = ext_vlss[ext_ind]
                id4del  = self.exts[ext_ind]['id']
                jex4dl  = [ex for ex in self.exts if id4del in ex.get('jext', [])]
                if app.msg_box( _('Delete tool?\n\n') + '\n'.join(['{}: {}'.format(flds[ind], ext_vls[ind]) 
                                                            for ind in range(len(flds))
                                                       ])
                              + ('\n\n'+'!'*50+_('\nDelete with joined tool(s)\n   ')+'\n   '.join([ex['nm'] for ex in jex4dl]) if jex4dl else '')
                              , app.MB_YESNO+app.MB_ICONQUESTION)!=app.ID_YES:
                    continue # while
                for lxr in [lxr for lxr,ext_id in self.ext4lxr.items() if ext_id==id4del]:
                    del self.ext4lxr[lxr]
                del self.exts[ext_ind]
                for ex in jex4dl:
                    del self.exts[self.exts.index(ex)]
                    self._do_acts('delete:'+str(ex['id']), '|keys|')
                vals['lst'] = min(ext_ind, len(self.exts)-1)
                what        = 'delete:'+str(id4del)

            pass;              #LOG and log('?? list _do_acts',)

            ext_ids     = [ext['id'] for ext in self.exts]
            url_ids     = [url['id'] for url in self.urls]
            if vals['tls']:
                ext_ind         = vals['lst']
                self.last_ext_id= ext_ids[ext_ind] if ext_ind!=-1 else ''
            if vals['urs']:
                url_ind         = vals['lst']
                self.last_url_id= url_ids[url_ind] if url_ind!=-1 else ''
            self._do_acts(what)
           #while True
       #def dlg_config
        
    def _dlg_adj_list(self):
        prs     = self.dlg_prs
        custs   = app.dlg_input_ex(10, _('Customization. Widths prefix "C"/"R" to align, "-" to hide.')
            , _('Width of Name    (min 100)')  , prs.get('nm'  , '150')
            , _('Width of Keys    (min  50)')  , prs.get('keys', '100')
            , _('Width of File    (min 150)')  , prs.get('file', '180')
            , _('Width of Params  (min 150)')  , prs.get('prms', '100')
            , _('Width of Folder  (min 100)')  , prs.get('ddir', '100')
            , _('Width of Lexers  (min  50)')  , prs.get('lxrs', 'C50')
            , _('Width of Capture (min  50)')  , prs.get('rslt', 'C50')
            , _('Width of Saving  (min  30)')  , prs.get('savs', 'C30')
            , _('List height  (min 200)')      , str(self.dlg_prs.get('h_list', 300))
            , _('Width of Url     (min 500)')  , prs.get('url',  '500')
    #       , _('Button width (min 70)')       , str(self.dlg_prs.get('w_btn', 90))
            )
        if custs is not None:
            def adapt2min(vmin, cval, can_hide=True):
                cval    = cval.upper()
                if can_hide and cval[0]=='-':   return cval
                cval    = cval.lstrip('-')
                c1st    = cval[0] if cval[0] in 'LRC' else ''
                cval    = cval.lstrip('LRC')
                return    c1st + str(max(vmin, int(cval)))
            self.dlg_prs['nm']      = adapt2min(100,     custs[0], False)
            self.dlg_prs['keys']    = adapt2min( 50,     custs[1], True)
            self.dlg_prs['file']    = adapt2min(150,     custs[2], True)
            self.dlg_prs['prms']    = adapt2min(150,     custs[3], True)
            self.dlg_prs['ddir']    = adapt2min(100,     custs[4], True)
            self.dlg_prs['lxrs']    = adapt2min( 50,     custs[5], True)
            self.dlg_prs['rslt']    = adapt2min( 50,     custs[6], True)
            self.dlg_prs['savs']    = adapt2min( 30,     custs[7], True)
            self.dlg_prs['h_list']  =       max(200, int(custs[8]))
            self.dlg_prs['url']     = adapt2min(250,     custs[9], True)
    #       self.dlg_prs['w_btn']   =       max( 70, int(custs[9]))
            open(EXTS_JSON, 'w').write(json.dumps(self.saving, indent=4))
       #def _dlg_adj_list

    def _dlg_main_tool(self, ext_id=0):
        if app.app_api_version()<FROM_API_VERSION:  return log_status(_('Need update CudaText'))
        lxrs_l  = app.lexer_proc(app.LEXER_GET_LEXERS, False) + ['(none)']
#       lxrs_l  = _get_lexers()
        nm4ids  = {ext['id']:ext['nm'] for ext in self.exts}
        nms     = [ext['nm'] for ext in self.exts]
        ids     = [ext['id'] for ext in self.exts]
        lxr_ind     = 0
        tool_ind    = ids.index(ext_id) if ext_id in ids else -1
#       focused     = 1
        DLG_W, DLG_H= GAP*3+300+400, GAP*4+300+23*2 -GAP+3
        vals    = dict(lxs=lxr_ind, tls=tool_ind)
        while True:
            lxrs_enm= ['{}{}'.format(lxr, '  >>>  {}'.format(nm4ids[self.ext4lxr[lxr]]) if lxr in self.ext4lxr else '')
                            for lxr in lxrs_l]
            cnts    =[dict(           tp='lb'   ,t=GAP+ 3           ,l=GAP          ,w=400  ,cap=_('&Lexer  >>>  main tool')) #  &l
                     ,dict(cid='lxs' ,tp='lbx'  ,t=GAP+23   ,h=300  ,l=GAP          ,w=400  ,items=lxrs_enm                 ) #  
                     ,dict(           tp='lb'   ,t=GAP+ 3           ,l=GAP+400+GAP  ,w=300  ,cap=_('&Tools')                ) #  &t
                     ,dict(cid='tls' ,tp='lbx'  ,t=GAP+23   ,h=300  ,l=GAP+400+GAP  ,w=300  ,items=nms                      ) #  
                     ,dict(cid='set' ,tp='bt'   ,t=GAP+23+300+GAP   ,l=GAP          ,w=97   ,cap=_('&Assign tool')          ) #  &a
                     ,dict(cid='del' ,tp='bt'   ,t=GAP+23+300+GAP   ,l=GAP+97+GAP   ,w=97   ,cap=_('&Break link')           ) #  &b
                     ,dict(cid='-'   ,tp='bt'   ,t=GAP+23+300+GAP   ,l=DLG_W-GAP-80 ,w=80   ,cap=_('Close')                 ) #  
                    ]
            btn, vals, *_t = dlg_wrapper(_('Main tool for lexers'), DLG_W, DLG_H, cnts, vals, focus_cid='lxs')
            if btn is None or btn=='-':    return
            lxr_ind     = vals['lxs']
            tool_ind    = vals['tls']
            changed     = False
            if False:pass
            elif (btn=='set' #'assign' 
            and   lxr_ind in range(len(lxrs_l)) 
            and   tool_ind in range(len(ids))):      #Assign
                lxr     = lxrs_l[lxr_ind]
                self.ext4lxr[lxr]   = ids[tool_ind]
                ext     = self.ext4id[str(ids[tool_ind])]
                if ','+lxr+',' not in ','+ext['lxrs']+',':
                    ext['lxrs'] = (ext['lxrs']+','+lxr).lstrip(',')
                changed = True

            elif (btn=='del' #'break' 
            and   lxr_ind in range(len(lxrs_l))
            and   lxrs_l[lxr_ind] in self.ext4lxr):  #Break
                del self.ext4lxr[lxrs_l[lxr_ind]]
                changed = True

            if changed:
                open(EXTS_JSON, 'w').write(json.dumps(self.saving, indent=4))
           #while True
       #def _dlg_main_tool
        
    def _dlg_usr_mcrs(self):
        DLG_W,  \
        DLG_H   = GAP*2+605, GAP+20+300+GAP+25+25+6
        bt_t1   = GAP+21+300+GAP
        bt_t2   = GAP+21+300+GAP+25
        bt_l1   = GAP
        bt_l2   = GAP+110+GAP
        bt_l3   = GAP+110+GAP+110+GAP
        bt_l4   = GAP+110+GAP+110+GAP+110+GAP
        umcr_vs = None
        vals    = dict(evl=False
                      ,lst=0)
        while True:
            if vals['evl']:
                umc_vals    = self._calc_umc_vals()
                umcr_vs     = [str(umc_vals[umc['nm']]) for umc in self.umacrs]
            itms    = (  [(_('Name'), '100'), (_('Current value')   if vals['evl'] else _('Expression'),'400'), (_('Comment'),'100')]
                      , [[um['nm'],           (umcr_vs[im]          if vals['evl'] else um['ex']),              um['co']]    for im,um in enumerate(self.umacrs)] )
#           itms    = (  [(_('Name'), '100'), (_('Expression'),'250'), (_('Current value'),'150'), (_('Comment'),'100')]
#                     , [[um['nm'],           um['ex'],                 umcr_vs[im],       um['co']]    for im,um in enumerate(self.umacrs)] )
            nempty  = '1' if self.umacrs else '0'
            cnts    =[dict(          tp='lb'    ,tid='evl'     ,l=GAP          ,w=400  ,cap=_('&Vars')                              )   # &v
                     ,dict(cid='evl',tp='ch'    ,t=GAP         ,l=GAP+105      ,w=80   ,cap=_('Expanded mac&ros')       ,act='1'    )   # &r
                     ,dict(cid='lst',tp='lvw'   ,t=GAP+21,h=300,l=GAP          ,w=605  ,items=itms                                  )   # 
                     ,dict(cid='edt',tp='bt'    ,t=bt_t1       ,l=bt_l1        ,w=110  ,cap=_('&Edit...')  ,props='1'   ,en=nempty  )   # &e  default
                     ,dict(cid='add',tp='bt'    ,t=bt_t1       ,l=bt_l2        ,w=110  ,cap=_('&Add...')                ,en=nempty  )   # &a
                     ,dict(cid='cln',tp='bt'    ,t=bt_t2       ,l=bt_l1        ,w=110  ,cap=_('Clo&ne')                 ,en=nempty  )   # &n
                     ,dict(cid='del',tp='bt'    ,t=bt_t2       ,l=bt_l2        ,w=110  ,cap=_('&Delete...')             ,en=nempty  )   # &d
                     ,dict(cid='up' ,tp='bt'    ,t=bt_t1       ,l=bt_l3        ,w=110  ,cap=_('&Up')                    ,en=nempty  )   # &u
                     ,dict(cid='dn' ,tp='bt'    ,t=bt_t2       ,l=bt_l3        ,w=110  ,cap=_('Do&wn')                  ,en=nempty  )   # &w
                     ,dict(cid='prj',tp='bt'    ,t=bt_t2       ,l=bt_l4+20     ,w=140  ,cap=_('Pro&ject macros...')                 )   # &j
                     ,dict(cid='hlp',tp='bt'    ,t=bt_t1       ,l=DLG_W-GAP-80 ,w=80   ,cap=_('Help')                               )   # 
                     ,dict(cid='-'  ,tp='bt'    ,t=bt_t2       ,l=DLG_W-GAP-80 ,w=80   ,cap=_('Close')                              )   # 
                    ]
            if not with_proj_man:
                cnts    = [cnt for cnt in cnts if 'cid' not in cnt or cnt['cid']!='prj']
            btn,vals,*_t= dlg_wrapper(_('User macros'), DLG_W, DLG_H, cnts, vals, focus_cid='lst')
            if btn is None or btn=='-':    return
            um_ind  = vals['lst']
            if btn=='hlp':
                dlg_help_vars()
                continue
            
            if btn=='prj':
                app.app_proc(app.PROC_EXEC_PLUGIN, 'cuda_project_man,config_proj')
                continue
            
            if btn=='add' or                          btn=='edt' and  um_ind!=-1:
                umc = self.umacrs[um_ind].copy()   if btn=='edt' else   {'nm':'', 'ex':'', 'co':''}
                um_cnts= [
                      dict(          tp='lb'    ,tid='nm'     ,l=GAP          ,w=100  ,cap=_('&Name:')        ) # &n
                     ,dict(cid='nm' ,tp='ed'    ,t=GAP        ,l=GAP+100      ,w=300                          ) #
                     ,dict(          tp='lb'    ,tid='ex'     ,l=GAP          ,w=100  ,cap=_('Val&ue:')       ) # &u
                     ,dict(cid='ex' ,tp='ed'    ,t=GAP+25     ,l=GAP+100      ,w=300                          ) #
                     ,dict(cid='fil',tp='bt'    ,t=GAP+50     ,l=GAP+100      ,w=100  ,cap=_('Add &file...')  ) # &f
                     ,dict(cid='dir',tp='bt'    ,t=GAP+50     ,l=GAP+200      ,w=100  ,cap=_('Add &dir...')   ) # &d
                     ,dict(cid='var',tp='bt'    ,t=GAP+50     ,l=GAP+300      ,w=100  ,cap=_('Add &var...')   ) # &v
                     ,dict(          tp='lb'    ,tid='co'     ,l=GAP          ,w=100  ,cap=_('&Comment:')     ) # &c
                     ,dict(cid='co' ,tp='ed'    ,t=GAP+75     ,l=GAP+100      ,w=300                          ) #
                     ,dict(cid='!'  ,tp='bt'    ,t=GAP+110    ,l=    400-140  ,w=70   ,cap=_('OK'),props='1'  ) #     default
                     ,dict(cid='-'  ,tp='bt'    ,t=GAP+110    ,l=GAP+400- 70  ,w=70   ,cap=_('Cancel')        ) #
                        ]
                um_fcsd = 'nm'
                while True:
                    um_btn,umc,*_t  = dlg_wrapper(_('Edit user macro var'), GAP+400+GAP, GAP+135+GAP, um_cnts, umc, focus_cid=um_fcsd)
#                   umfid,  \
#                   umch    = dlg_wrapper(_('Edit user macro var'), GAP+400+GAP, GAP+135+GAP, um_cnts, umc, focus_cid=um_fcsd)
                    if um_btn is None or um_btn=='-':
                        umc     = None  # ='No changes'
                        break #while um
                    if um_btn=='fil':
                        ans_file = app.dlg_file(True, '', '', '')
                        if ans_file is not None: 
                            umc['ex']   = (umc['ex'] +' '+ ans_file).lstrip()
                        um_fcsd  = 'ex'
                    if um_btn=='dir':
                        ans_dir = app.dlg_dir('')
                        if ans_dir is not None: 
                            umc['ex']   = (umc['ex'] +' '+ ans_dir).lstrip()
                        um_fcsd  = 'ex'
                    if um_btn=='var':
                        umc['ex']  = append_prmt(umc['ex'], self.umacrs, excl_umc=umc['nm'])
                        um_fcsd  = 'ex'
                    
                    if um_btn=='!':
                        if not umc['nm']:
                            app.msg_box(_('Set Name'), app.MB_OK)
                            um_fcsd     = 'nm'
                            continue #while um
                        if not umc['ex']:
                            app.msg_box(_('Set Value'), app.MB_OK)
                            um_fcsd     = 'ex'
                            continue #while um
                        break #while um
               #while um
                if umc is None: # =='No changes'
                    continue #while    No changes    
                if btn=='edt':
                    self.umacrs[um_ind].update(umc)
                else: #   'add'
                    self.umacrs += [umc]
                    um_ind      = len(self.umacrs)-1
                    vals['lst'] = um_ind

            if btn=='cln' and  um_ind!=-1: #Clone
                umc         = self.umacrs[um_ind].copy()
                umc['nm']  += ' clone'
                self.umacrs+= [umc]
                um_ind      = len(self.umacrs)-1
                vals['lst'] = um_ind

            if btn=='del' and  um_ind!=-1: 
                if app.msg_box(  _('Delete Macro?\n\n')+ '\n'.join([
                                 _('Name: {}').format(   self.umacrs[um_ind]['nm'])
                                ,_('Value: {}').format(  self.umacrs[um_ind]['ex']) 
                                ,_('Comment: {}').format(self.umacrs[um_ind]['co'])]), app.MB_YESNO+app.MB_ICONQUESTION)!=app.ID_YES:
                    continue #while    No changes
                del self.umacrs[um_ind]
                um_ind      = min(um_ind, len(self.umacrs)-1)
                vals['lst'] = um_ind

            elif btn=='up' and um_ind>0: #Up
                (self.umacrs[um_ind-1]
                ,self.umacrs[um_ind  ]) = (self.umacrs[um_ind  ]
                                          ,self.umacrs[um_ind-1])
                um_ind      = um_ind-1
                vals['lst'] = um_ind
            elif btn=='dn' and um_ind<(len(self.umacrs)-1): #Down
                (self.umacrs[um_ind  ]
                ,self.umacrs[um_ind+1]) = (self.umacrs[um_ind+1]
                                          ,self.umacrs[um_ind  ])
                um_ind      = um_ind+1
                vals['lst'] = um_ind

            # Save changes
            open(EXTS_JSON, 'w').write(json.dumps(self.saving, indent=4))
           #while True
       #def _dlg_usr_mcrs

    def _dlg_exts_for_join(self, ext_ids=[]):
        ext4jn  = [ex                                   for ex in self.exts if not ex.get('jext')]
        ext_nms = [ex['nm']                             for ex in ext4jn]
        sels    = ['1' if ex['id'] in ext_ids else '0'  for ex in ext4jn]
        crt     = str(sels.index('1') if '1' in sels else 0)

        cnts    =[dict(cid='exs',tp='ch-lbx',t=GAP,h=400    ,l=GAP          ,w=300  ,items=ext_nms          ) #
                 ,dict(cid='!'  ,tp='bt'    ,t=GAP+400+GAP  ,l=    300-140  ,w=70   ,cap=_('OK'),props='1'  ) #  default
                 ,dict(cid='-'  ,tp='bt'    ,t=GAP+400+GAP  ,l=GAP+300- 70  ,w=70   ,cap=_('Cancel')        ) #  
                ]
        vals    = dict(exs=(crt,sels))
        btn,    \
        vals,*_t= dlg_wrapper(_('Select tools for join'), GAP+300+GAP, GAP+400+GAP+24+GAP, cnts, vals, focus_cid='exs')
#       fid,    \
#       chds    = dlg_wrapper(_('Select tools for join'), GAP+300+GAP, GAP+400+GAP+24+GAP, cnts, vals, focus_cid='exs')
        if btn is None or btn=='-': return None
        crt,sels= vals['exs']
        ext_ids = [ext4jn[ind]['id'] for ind in range(len(sels)) if sels[ind]=='1']
        return ext_ids
       #def _dlg_exts_for_join
        
    def _dlg_url_prop(self, src_url, keys=None, for_ed='1'):
        keys_json   = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'keys.json'
        if keys is None:
            keys    = apx._json_loads(open(keys_json).read()) if os.path.exists(keys_json) else {}
        src_kys     = get_keys_desc('cuda_exttools,browse', src_url['id'], keys)

        ed_url      = copy.deepcopy(src_url)

        GAP2            = GAP*2    
        PRP1_W, PRP1_L  = (100,     GAP)
        PRP2_W, PRP2_L  = (400-GAP, PRP1_L+    PRP1_W+GAP)
        PRP3_W, PRP3_L  = (100,     PRP2_L+GAP+PRP2_W)
        PROP_T          = [GAP*ind+25*(ind-1) for ind in range(10)]   # max 20 rows
        DLG_W, DLG_H    = PRP3_L+PRP3_W+GAP, PROP_T[6]-21
        focus_cid   = 'nm'
        while True:
            ed_kys  = get_keys_desc('cuda_exttools,browse', ed_url['id'], keys)
            vals    =       dict(nm  =ed_url['nm']
                                ,url =ed_url['url']
                                ,keys=ed_kys
                                )
            cnts    =[dict(           tp='lb'   ,tid='nm'      ,l=PRP1_L   ,w=PRP1_W   ,cap=_('&Name:')                     ) # &n
                     ,dict(cid='nm'  ,tp='ed'   ,t=PROP_T[1]   ,l=PRP2_L   ,w=PRP2_W                                        ) #

                     ,dict(           tp='lb'   ,tid='url'     ,l=PRP1_L   ,w=PRP1_W   ,cap=_('&URL:')                      ) # &u
                     ,dict(cid='url' ,tp='ed'   ,t=PROP_T[2]   ,l=PRP2_L   ,w=PRP2_W                                        ) #
                     ,dict(cid='?mcr',tp='bt'   ,tid='url'     ,l=PRP3_L   ,w=PRP3_W   ,cap=_('&Macro...')                  ) # &m
                                              
                     ,dict(           tp='lb'   ,tid='keys'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Hotkey:')                    ) #
                     ,dict(cid='keys',tp='ed'   ,t=PROP_T[3]   ,l=PRP2_L   ,w=PRP2_W                       ,props='1,0,1'   ) #     ro,mono,border
#                    ,dict(cid='?key',tp='bt'   ,tid='keys'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('Assi&gn...')                 ) # &g

                     ,dict(cid='help',tp='bt'   ,t=PROP_T[4]+9 ,l=GAP      ,w=PRP3_W       ,cap=_('Help')                   ) #
                     ,dict(cid='prjs',tp='bt'   ,t=PROP_T[4]+9 ,l=PRP2_L   ,w=PRP3_W       ,cap=_('Pro&ject...')            ) # &j
                     ,dict(cid='!'   ,tp='bt'   ,t=PROP_T[4]+9 ,l=DLG_W-GAP*2-100*2,w=100  ,cap=_('OK')    ,props='1'       ) #     default
                     ,dict(cid='-'   ,tp='bt'   ,t=PROP_T[4]+9 ,l=DLG_W-GAP*1-100*1,w=100  ,cap=_('Cancel')                 ) #
                    ]
            if not with_proj_man:
                cnts    = [cnt for cnt in cnts if 'cid' not in cnt or cnt['cid']!='prjs']
            btn,    \
            vals,*_t= dlg_wrapper(_('URL properties'), DLG_W, DLG_H, cnts, vals, focus_cid=focus_cid)
#           fid,    \
#           chds    = dlg_wrapper(_('URL properties'), DLG_W, DLG_H, cnts, vals, focus_cid=focus_cid)
            if btn is None or btn=='-': return None
            ed_url['nm']    =   vals['nm']
            ed_url['url']   =   vals['url']

            if btn=='!':
                # Check props
                if False:pass
                elif not ed_url['nm']:
                    app.msg_box(_('Set Name'), app.MB_OK)
                    focus_cid   = 'nm'
                    continue #while
                    
                pass;          #LOG and log('save    src_ext={}',src_ext)
                pass;          #LOG and log('save ed_ext={}',ed_ext)
                if src_url==ed_url and src_kys==ed_kys:
                    pass;      #LOG and log('ok, no chngs')
                    return False
                src_url.update(ed_url)
                pass;          #LOG and log('ok, fill src_ext={}',src_ext)
                return True

            if False:pass
            elif btn=='help':
                dlg_help_vars()
                continue #while
            elif btn=='prjs':
                app.app_proc(app.PROC_EXEC_PLUGIN, 'cuda_project_man,config_proj')
                continue #while
            elif btn=='?mcr':   #Append param {*}
                ed_url['url']   = append_prmt(ed_url['url'], self.umacrs)
                focus_cid       = 'url'

            elif btn=='?key':
                app.dlg_hotkeys('cuda_exttools,browse,'+str(ed_url['id']))
                keys    = apx._json_loads(open(keys_json).read()) if os.path.exists(keys_json) else {}
           #while True:
       #def _dlg_url_prop
        
    def _dlg_ext_prop(self, src_ext, keys=None, for_ed='1'):
        if app.app_api_version()<FROM_API_VERSION:  return log_status(_('Need update CudaText'))
        keys_json   = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'keys.json'
        if keys is None:
            keys    = apx._json_loads(open(keys_json).read()) if os.path.exists(keys_json) else {}
        src_kys     = get_keys_desc('cuda_exttools,run', src_ext['id'], keys)

        ed_ext      = copy.deepcopy(src_ext)
        
        GAP2            = GAP*2    
        PRP1_W, PRP1_L  = (100,     GAP)
        PRP2_W, PRP2_L  = (400-GAP, PRP1_L+    PRP1_W+GAP)
        PRP3_W, PRP3_L  = (100,     PRP2_L+GAP+PRP2_W)
        PROP_T          = [GAP*ind+25*(ind-1) for ind in range(20)]   # max 20 rows
        DLG_W, DLG_H    = PRP3_L+PRP3_W+GAP, PROP_T[17]-21
        
        jex_ids         = ed_ext.get('jext', None)
        joined          = jex_ids is not None
        sel_jext        = 0
        focus_cid       = 'nm'
        while True:
            ed_kys  = get_keys_desc('cuda_exttools,run', ed_ext['id'], keys)
#           val_savs= self.savs_vals.index(ed_ext['savs']) if ed_ext is not None else 0
#           val_rslt= self.rslt_vals.index(ed_ext['rslt']) if ed_ext is not None else 0
            val_savs= self.savs_vals.index(ed_ext['savs'] if ed_ext else SAVS_N)        # def is "not save"
            val_rslt= self.rslt_vals.index(ed_ext['rslt'] if ed_ext else RSLT_OP)       # def is "to panel"

            
            jext_nms= [self.ext4id[str(eid)]['nm'] for eid in jex_ids] if joined else None
            
            main_for= ','.join([lxr for (lxr,eid) in self.ext4lxr.items() if eid==ed_ext['id']])
            more_s  = json.dumps(_adv_prop('get-dict', ed_ext)).strip('{}').strip()

            vals    =       dict(nm  =ed_ext['nm']
                                ,lxrs=ed_ext['lxrs']
                                ,main=main_for
                                ,savs=val_savs
                                ,keys=ed_kys
                                ,more=more_s
                                )
            if joined:
                vals.update(dict(seri=sel_jext))
            else:
                vals.update(dict(file=ed_ext['file']
                                ,shll=('1' if ed_ext['shll'] else '0')
                                ,prms=ed_ext['prms']
                                ,ddir=ed_ext['ddir']
                                ,encd=ed_ext['encd']
                                ,rslt=val_rslt
                                ,pttn=ed_ext['pttn']
                                ))
            #NOTE: edit cnts
            cnts    = ([]
                     +[dict(           tp='lb'   ,tid='nm'      ,l=PRP1_L   ,w=PRP1_W   ,cap=_('&Name:')                        )] # &n
                     +[dict(cid='nm'  ,tp='ed'   ,t=PROP_T[1]   ,l=PRP2_L   ,w=PRP2_W                                           )] #
                    +([]                                       
                     +[dict(           tp='lb'   ,tid='seri'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Se&ries:')                      )] # &r
                     +[dict(cid='seri',tp='lbx'  ,t=PROP_T[2]   ,l=PRP2_L   ,w=PRP2_W    ,b=PROP_T[6]-GAP,items=jext_nms        )] #
                     +[dict(cid='?ser',tp='bt'   ,t=PROP_T[2]   ,l=PRP3_L   ,w=PRP3_W   ,cap=_('&Select...')    ,en=for_ed      )] # &s
                     +[dict(cid='view',tp='bt'   ,t=PROP_T[3]-4 ,l=PRP3_L   ,w=PRP3_W   ,cap=_('Vie&w...')      ,en=for_ed      )] # &w
                     +[dict(cid='up'  ,tp='bt'   ,t=PROP_T[4]+2 ,l=PRP3_L   ,w=PRP3_W   ,cap=_('&Up')           ,en=for_ed      )] # &u
                     +[dict(cid='dn'  ,tp='bt'   ,t=PROP_T[5]-2 ,l=PRP3_L   ,w=PRP3_W   ,cap=_('&Down')         ,en=for_ed      )] # &d
                    if joined else []
                     +[dict(           tp='lb'   ,tid='file'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('&File name:')                   )] # &f
                     +[dict(cid='file',tp='ed'   ,t=PROP_T[2]   ,l=PRP2_L   ,w=PRP2_W                                           )] #
                     +[dict(cid='?fil',tp='bt'   ,tid='file'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('&Browse...')    ,en=for_ed      )] # &b
                     +[dict(cid='shll',tp='ch'   ,t=PROP_T[3]-2 ,l=PRP2_L   ,w=PRP2_W   ,cap=_('&Shell command'),en=for_ed         # &s
                                                                                        ,hint=_('Run the tool via OS shell interpreter (e.g. Bash on Unix, Cmd on Windows)')    )]
                                                 
                     +[dict(           tp='lb'   ,tid='prms'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('&Parameters:')                  )] # &p
                     +[dict(cid='prms',tp='ed'   ,t=PROP_T[4]   ,l=PRP2_L   ,w=PRP2_W                                           )] #
                     +[dict(cid='?mcr',tp='bt'   ,tid='prms'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('A&dd...')       ,en=for_ed      )] # &a
                                                 
                     +[dict(           tp='lb'   ,tid='ddir'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('&Initial folder:')              )] # &i
                     +[dict(cid='ddir',tp='ed'   ,t=PROP_T[5]   ,l=PRP2_L   ,w=PRP2_W                                           )] #
                     +[dict(cid='?dir',tp='bt'   ,tid='ddir'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('B&rowse...')    ,en=for_ed      )] # &r
                    )
                     +[dict(           tp='lb'   ,tid='lxrs'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Lexers:')                       )] #
                     +[dict(cid='lxrs',tp='ed'   ,t=PROP_T[6]   ,l=PRP2_L   ,w=PRP2_W                       ,props='1,0,1'      )] #     ro,mono,border
                     +[dict(cid='?lxr',tp='bt'   ,tid='lxrs'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('Le&xers...')    ,en=for_ed      )] # &x
                                                 
                     +[dict(           tp='lb'   ,tid='main'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Main for:')                     )] #
                     +[dict(cid='main',tp='ed'   ,t=PROP_T[7]   ,l=PRP2_L   ,w=PRP2_W                       ,props='1,0,1'      )] #     ro,mono,border
                     +[dict(cid='?man',tp='bt'   ,tid='main'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('Set &main...')  ,en=for_ed      )] # &m
                                                 
                     +[dict(           tp='lb'   ,tid='savs'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Sa&ve before:')                 )] # &v
                     +[dict(cid='savs',tp='cb-ro',t=PROP_T[8]   ,l=PRP2_L   ,w=PRP2_W   ,items=self.savs_caps   ,en=for_ed      )] #
                                              
                     +[dict(           tp='lb'   ,tid='keys'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Hotkey:')                       )] #
                     +[dict(cid='keys',tp='ed'   ,t=PROP_T[9]   ,l=PRP2_L   ,w=PRP2_W                       ,props='1,0,1'      )] #     ro,mono,border
#                    +[dict(cid='?key',tp='bt'   ,tid='keys'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('Assi&gn...')    ,en=for_ed      )] # &g
                    +([] if joined else []                     
                     +[dict(           tp='lb'   ,tid='rslt'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('&Capture output:')              )] # &c
                     +[dict(cid='rslt',tp='cb-ro',t=PROP_T[11]  ,l=PRP2_L   ,w=PRP2_W   ,items=self.rslt_caps   ,en=for_ed      )] 
                     +[dict(           tp='lb'   ,tid='encd'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Encoding:')                     )] #
                     +[dict(cid='encd',tp='ed'   ,t=PROP_T[12]  ,l=PRP2_L   ,w=PRP2_W                       ,props='1,0,1'      )] #     ro,mono,border
                     +[dict(cid='?enc',tp='bt'   ,tid='encd'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('S&elect...')    ,en=for_ed      )] # &
                     +[dict(           tp='lb'   ,tid='pttn'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Pattern:')                      )] #
                     +[dict(cid='pttn',tp='ed'   ,t=PROP_T[13]  ,l=PRP2_L   ,w=PRP2_W                       ,props='1,0,1'      )] #     ro,mono,border
                     +[dict(cid='?ptn',tp='bt'   ,tid='pttn'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('Se&t...')       ,en=for_ed      )] # &e
                    )                                         
                     +[dict(           tp='lb'   ,tid='more'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Advanced:')                     )] #
                     +[dict(cid='more',tp='ed'   ,t=PROP_T[14]  ,l=PRP2_L   ,w=PRP2_W                       ,props='1,0,1'      )] #     ro,mono,border
                     +[dict(cid='?mor',tp='bt'   ,tid='more'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('Set...')        ,en=for_ed      )] #
                    +([] if joined else []                     
                     +[dict(cid='help',tp='bt'   ,t=PROP_T[15]+9,l=GAP      ,w=PRP3_W       ,cap=_('Help')      ,en=for_ed      )] #
                     +[dict(cid='prjs',tp='bt'   ,t=PROP_T[15]+9,l=PRP2_L   ,w=PRP3_W       ,cap=_('Pro&ject...'),en=for_ed     )] # &j
                    )                                         
                     +[dict(cid='!'   ,tp='bt'   ,t=PROP_T[15]+9,l=DLG_W-GAP*2-100*2,w=100  ,cap=_('OK')    ,props='1',en=for_ed)] #     default
                     +[dict(cid='-'   ,tp='bt'   ,t=PROP_T[15]+9,l=DLG_W-GAP*1-100*1,w=100  ,cap=_('Cancel')                    )] #
                    )
            if not with_proj_man:
                cnts    = [cnt for cnt in cnts if 'cid' not in cnt or cnt['cid']!='prjs']
            btn,    \
            vals,   \
            fid,    \
            chds    = dlg_wrapper(_('Tool properties'), DLG_W, DLG_H, cnts, vals, focus_cid=focus_cid)
#           pass;               LOG and log('fid,chds={}',(fid,chds))
            if btn is None or btn=='-': return None
            
            focus_cid           = fid if fid else focus_cid
            
            ed_ext['nm']        =   vals[  'nm']
            ed_ext['lxrs']      =   vals['lxrs']
            ed_ext['savs']      = self.savs_vals[int(
                                    vals['savs'])]
            if joined:
                sel_jext        =   vals['seri']
            if not joined:      
                ed_ext['file']  =   vals['file']
                ed_ext['shll']  =   vals['shll']=='1'
                ed_ext['prms']  =   vals['prms']
                ed_ext['ddir']  =   vals['ddir']
                ed_ext['rslt']  = self.rslt_vals[int(
                                    vals['rslt'])]
                ed_ext['encd']  =   vals['encd']

            if btn=='!':
                # Check props
                if False:pass
                elif not ed_ext['nm']:
                    app.msg_box(_('Set Name'), app.MB_OK)
                    focus_cid   = 'nm'
                    continue #while
                elif not joined and not ed_ext['file']:
                    app.msg_box(_('Set File name'), app.MB_OK)
                    focus_cid   = 'file'
                    continue #while
                    
                pass;          #LOG and log('save    src_ext={}',src_ext)
                pass;          #LOG and log('save ed_ext={}',ed_ext)
                if src_ext==ed_ext and src_kys==ed_kys:
                    pass;      #LOG and log('ok, no chngs')
                    return False
                src_ext.update(ed_ext)
                for fld in [k for k in src_ext if k not in ed_ext]:
                    src_ext.pop(fld, None)
                pass;          #LOG and log('ok, fill src_ext={}',src_ext)
                return True

            if False:pass
            elif btn=='help':
                dlg_help_vars()
                continue #while
            elif btn=='prjs':
                app.app_proc(app.PROC_EXEC_PLUGIN, 'cuda_project_man,config_proj')
                continue #while

            if joined and btn=='view' and sel_jext!=-1: # View one of joined
                self._dlg_ext_prop(self.ext4id[str(jex_ids[sel_jext])], keys, for_ed='0')
            
            if joined and btn=='?ser': # Select exts to join
                jex_ids_new = self._dlg_exts_for_join(jex_ids)
                if jex_ids_new is not None and len(jex_ids_new)>1:
                    jex_ids = ed_ext['jext'] = jex_ids_new
                continue #while

            if joined and btn=='up' and sel_jext>0:
                (jex_ids[sel_jext-1] 
                ,jex_ids[sel_jext  ])   =   (jex_ids[sel_jext  ] 
                                            ,jex_ids[sel_jext-1])
                sel_jext               -= 1
            if joined and btn=='dn' and sel_jext<len(jex_ids):
                (jex_ids[sel_jext  ] 
                ,jex_ids[sel_jext+1])   =   (jex_ids[sel_jext+1] 
                                            ,jex_ids[sel_jext  ])
                sel_jext               += 1

            if btn=='?man': #Lexer main tool
                self._dlg_main_tool(ed_ext['id'])
                continue #while
            
            elif btn=='?fil':
                file4run= app.dlg_file(True, '!'+ed_ext['file'], '', '')# '!' to disable check "filename exists"
                if file4run is not None:
                    ed_ext['file']  = file4run
                    focus_cid       = 'file'
            
            elif btn=='?dir':
                new_dir = app.dlg_dir(ed_ext['ddir'])
                if new_dir is not None:
                    ed_ext['ddir']  = new_dir
                    focus_cid       = 'ddir'
#               file4dir= app.dlg_file(True, '!', ed_ext['ddir'], '')   # '!' to disable check "filename exists"
#               if file4dir is not None:
#                   ed_ext['ddir']  = os.path.dirname(file4dir)
#                   focus_cid       = 'ddir'

            elif btn=='?mcr':           #Append macro to...
                if False:pass
                elif fid=='file':       #...File
                    ed_ext['file']  = append_prmt(ed_ext['file'], self.umacrs)
                elif fid=='ddir':       #...InitDir
                    ed_ext['ddir']  = append_prmt(ed_ext['ddir'], self.umacrs)
                else:                   #...Params
                    ed_ext['prms']  = append_prmt(ed_ext['prms'], self.umacrs)

            elif btn=='?key':
                app.dlg_hotkeys('cuda_exttools,run,'+str(ed_ext['id']))
                keys    = apx._json_loads(open(keys_json).read()) if os.path.exists(keys_json) else {}
            
            elif btn=='?lxr':   #Lexers only
                lxrs    = ','+ed_ext['lxrs']+','
                lxrs_l  = app.lexer_proc(app.LEXER_GET_LEXERS, False) + ['(none)']
#               lxrs_l  = _get_lexers()
                sels    = ['1' if ','+lxr+',' in lxrs else '0' for lxr in lxrs_l]
                crt     = str(sels.index('1') if '1' in sels else 0)

                lx_cnts =[dict(cid='lxs',tp='ch-lbx',t=GAP,h=400    ,l=GAP          ,w=200  ,items=lxrs_l           ) #
                         ,dict(cid='!'  ,tp='bt'    ,t=GAP+400+GAP  ,l=    200-140  ,w=70   ,cap=_('OK'),props='1'  ) #  default
                         ,dict(cid='-'  ,tp='bt'    ,t=GAP+400+GAP  ,l=GAP+200- 70  ,w=70   ,cap=_('Cancel')        ) #  
                        ]
                lx_vals = dict(lxs=(crt,sels))
                lx_btn, \
                lx_vals,\
                *_t     = dlg_wrapper(_('Select lexers'), GAP+200+GAP, GAP+400+GAP+24+GAP, lx_cnts, lx_vals, focus_cid='lxs')
#               lx_fid, \
#               lx_chds = dlg_wrapper(_('Select lexers'), GAP+200+GAP, GAP+400+GAP+24+GAP, lx_cnts, lx_vals, focus_cid='lxs')
                if lx_btn=='!':
                    crt,sels= lx_vals['lxs']
                    lxrs    = [lxr for (ind,lxr) in enumerate(lxrs_l) if sels[ind]=='1']
                    ed_ext['lxrs'] = ','.join(lxrs)
            
            elif btn=='?enc':
                enc_nms = get_encoding_names()
                enc_ind = app.dlg_menu(app.MENU_LIST_ALT, '\n'.join(enc_nms), caption=_('Encodings'))
                if enc_ind is not None:
                    ed_ext['encd'] = enc_nms[enc_ind].split('\t')[0]

            elif btn=='?ptn':   #Pattern
                pass;          #LOG and log('?? ed_ext[pttn-data]={}',ed_ext['pttn-data'])
                (new_pttn,new_test)     = self._dlg_pattern(ed_ext['pttn'], ed_ext.get('pttn-test', ''), os.path.basename(ed_ext['file']))
                if new_pttn is not None:
                    ed_ext['pttn']      = new_pttn
                    ed_ext['pttn-test'] = new_test
                pass;          #LOG and log('ok ed_ext[pttn-data]={}',ed_ext['pttn-data'])
            
            elif btn=='?mor':   #Advanced
                ad_vals = {}
                ad_cnts = []
                for (i, a) in enumerate(ADV_PROPS):
                    ad_key  = a['key']
                    ad_vals[ad_key]   = ed_ext.get(ad_key, a['def'])
                    ad_cnts+=[
                     dict(           tp='lb',t=GAP+i*50     ,l=GAP+150      ,w=450  ,cap=a['cap'],hint=a['hnt'] )
                    ,dict(           tp='lb',tid=ad_key     ,l=GAP          ,w=150  ,cap=f('{}:', ad_key)       )
                    ,dict(cid=ad_key,tp='ed',t=GAP+i*50+18  ,l=GAP+150      ,w=450                              )
                          ]
                   #for (i, a)
                avd_h   = len(ADV_PROPS)*50
                ad_cnts   += [
                     dict(cid='!'   ,tp='bt',t=GAP+avd_h+GAP,l=    600-140  ,w=70   ,cap=_('OK')     ,props='1' ) # default
                    ,dict(cid='-'   ,tp='bt',t=GAP+avd_h+GAP,l=GAP+600- 70  ,w=70   ,cap=_('Cancel')            )
                            ]
                ad_btn, \
                ad_vals,\
                *_t     = dlg_wrapper(_('Advanced properties'), GAP+600+GAP, GAP+avd_h+GAP+24+GAP+3, ad_cnts, ad_vals, focus_cid='-')
#               ad_fid, \
#               ad_chds = dlg_wrapper(_('Advanced properties'), GAP+600+GAP, GAP+avd_h+GAP+24+GAP+3, ad_cnts, ad_vals, focus_cid='-')
                if ad_btn is None or ad_btn=='-':   continue#while
                for a in enumerate(ADV_PROPS):
                    if ad_vals[a['key']]==a['def']:
                        ed_ext.pop(a['key'], None)
                    else:
                        ed_ext[    a['key']]= ad_vals[a['key']]
                   #for a
           #while True
       #def _dlg_ext_prop

    def _dlg_pattern(self, pttn_re, pttn_test, run_nm):
        pass;                  #LOG and log('pttn_re, pttn_test={}',(pttn_re, pttn_test))
        grp_dic = {}
        if pttn_re and pttn_test:
            grp_dic = re.search(pttn_re, pttn_test).groupdict('') if re.search(pttn_re, pttn_test) is not None else {}
        
        RE_REF  = 'https://docs.python.org/3/library/re.html'
        DLG_W,  \
        DLG_H   = GAP+550+GAP, GAP+250+3#+GAP
        cnts    =[dict(cid=''          ,tp='ln-lb'  ,t=GAP          ,l=GAP              ,w=300              ,cap=_('&Regular expression:')
                                                                                                            ,props=RE_REF                ) # &r
                 ,dict(cid='pttn_re'   ,tp='ed'     ,t=GAP+18       ,l=GAP              ,r=DLG_W-GAP*2-70                                ) #
                 ,dict(cid='apnd'      ,tp='bt'     ,tid='pttn_re'  ,l=DLG_W-GAP*1-70   ,w=70               ,cap=_('&Add...')
                                                                                                            ,hint='Append named group'   ) # &a
#                ,dict(cid='help'      ,tp='bt'     ,tid='pttn_re'  ,l=DLG_W-GAP*1-70   ,w=70               ,cap='&?..'                  ) # &?
                 # Testing                                                                                         
                 ,dict(cid=''          ,tp='lb'     ,t= 60          ,l=GAP              ,w=300              ,cap=_('Test "&Output line":')) # &o
                 ,dict(cid='pttn_test' ,tp='ed'     ,t= 60+18       ,l=GAP              ,r=DLG_W-GAP*2-70                                ) #
                 ,dict(cid='test'      ,tp='bt'     ,tid='pttn_test',l=DLG_W-GAP*1-70   ,w=70               ,cap=_('&Test')              ) # &t
                                                                                                                               
                 ,dict(cid=''          ,tp='lb'     ,t=110+GAP*0+23*0   ,l=GAP+ 80      ,w=300              ,cap=_('Testing results')    ) #
                 ,dict(cid=''          ,tp='lb'     ,tid='file'         ,l=GAP          ,w=80               ,cap=_('Filename:')          ) #
                 ,dict(cid='file'      ,tp='ed'     ,t=110+GAP*0+23*1   ,l=GAP+ 80      ,r=DLG_W-GAP*2-70               ,props='1,0,1'   ) #   ro,mono,border
                 ,dict(cid=''          ,tp='lb'     ,tid='line'         ,l=GAP          ,w=80               ,cap=_('Line:')              ) #
                 ,dict(cid='line'      ,tp='ed'     ,t=110+GAP*1+23*2   ,l=GAP+ 80      ,r=DLG_W-GAP*2-70               ,props='1,0,1'   ) #   ro,mono,border
                 ,dict(cid=''          ,tp='lb'     ,tid='col'          ,l=GAP          ,w=80               ,cap=_('Column:')            ) #
                 ,dict(cid='col'       ,tp='ed'     ,t=110+GAP*2+23*3   ,l=GAP+ 80      ,r=DLG_W-GAP*2-70               ,props='1,0,1'   ) #   ro,mono,border
                 # Preset                                                                                          
                 ,dict(cid='load'      ,tp='bt'     ,t=DLG_H-GAP-24 ,l=GAP              ,w=130              ,cap=_('Load &preset...')    ) # &p
                 ,dict(cid='save'      ,tp='bt'     ,t=DLG_H-GAP-24 ,l=GAP+130+GAP      ,w=130              ,cap=_('&Save as preset...') ) # &s
                 # OK                                                                                              
                 ,dict(cid='ok'        ,tp='bt'     ,t=DLG_H-GAP-24 ,l=    550-140      ,w=70               ,cap=_('OK'),props='1'       ) #   default
                 ,dict(cid='cancel'    ,tp='bt'     ,t=DLG_H-GAP-24 ,l=GAP+550- 70      ,w=70               ,cap=_('Cancel')             ) #
                ]
        while True:
            vals    = dict(  
             pttn_re    =pttn_re
            ,pttn_test  =pttn_test
            ,file       =grp_dic.get('file', '')
            ,line       =grp_dic.get('line', '')
            ,col        =grp_dic.get('col', '')
                        )
            btn,    \
            vals,*_t= dlg_wrapper(_('Tool "{}" output pattern').format(run_nm), DLG_W, DLG_H, cnts, vals, focus_cid='pttn_re')
#           fid,    \
#           chds    = dlg_wrapper(_('Tool "{}" output pattern').format(run_nm), DLG_W, DLG_H, cnts, vals, focus_cid='pttn_re')
            if btn is None or btn=='cancel':    return (None, None)
            pttn_re = vals['pttn_re']
            pttn_test=vals['pttn_test']

            if False:pass
            elif btn == 'ok':
                return (pttn_re, pttn_test)
            
            elif btn == 'apnd':
                grps    = [['(?P<file>)' , _('Filename (default - current file name)')]
                          ,['(?P<line>)' , _('Number of line (default - 1)')]
                          ,['(?P<col>)'  , _('Number of column (default - 1)')]
                          ,['(?P<line0>)', _('Number of line (0-based, default - 0)')]
                          ,['(?P<col0>)' , _('Number of column (0-based, default - 0)')]
                        ]
                grp_i   = app.dlg_menu(app.MENU_LIST_ALT, '\n'.join(['\t'.join(g) for g in grps]), caption=_('Pattern variables'))
                if grp_i is not None:
                    pttn_re += grps[grp_i][0]
                
#           elif btn == 'help':
#               app.msg_box(''
#                          +'These groups will be used for navigation:'
#                          +'\n   (?P<file>_) for filename (default - current file name),'
#                          +'\n   (?P<line>_) for number of line (default - 1),'
#                          +'\n   (?P<col>_) for number of column (default - 1).'
#                          +'\n   (?P<line0>_) for number of line (0-based, default - 0),'
#                          +'\n   (?P<col0>_) for number of column (0-based, default - 0).'
#                          +'\n'
#                          +'\nFull syntax documentation: https://docs.python.org/3/library/re.html'
#               , app.MB_OK)
            
            elif btn == 'test':
                try:
                    grp_dic = re.search(pttn_re, pttn_test).groupdict('') if re.search(pttn_re, pttn_test) is not None else {}
                except Exception as e:
                    app.msg_box(_('RegEx is incorrect: '+str(e)), app.MB_OK+app.MB_ICONERROR)
            
            elif btn == 'load':
                ps_nms  = ['{}\t{}'.format(ps['name'], ps['run']) for ps in self.preset]
                ps_ind  = app.dlg_menu(app.MENU_LIST, '\n'.join(ps_nms), caption=_('Ready patterns'))
                if ps_ind is not None:
                    pttn_re     = self.preset[ps_ind]['re']
                    pttn_test   = self.preset[ps_ind].get('test', '')
                    grp_dic     = re.search(pttn_re, pttn_test).groupdict('') if re.search(pttn_re, pttn_test) is not None else {}
            
            elif btn == 'save':
                if not pttn_re:
                    app.msg_box(_('Set "Regular expression"'), app.MB_OK)
                    continue #while
                nm_ps  = app.dlg_input(_('Name for preset ({})').format(run_nm), run_nm)
                if nm_ps is None or not nm_ps:
                    continue #while
                self.preset    += [{'name':nm_ps
                                  ,'run':run_nm
                                  ,'re':pttn_re
                                  ,'test':pttn_test
                                  }]
                open(EXTS_JSON, 'w').write(json.dumps(self.saving, indent=4))
           #while True
        pass
       #def _dlg_pattern
        
    def _fill_ext(self, ext):
        ext.pop('capt', None)   # obsolete
        ext.pop('name', None)   # obsolete
        if not ext['nm']:
            ext['nm']='tool'+str(random.randint(100, 999))
        ext['ddir'] = ext.get('ddir', '{FileDir}')
#       ext['ddir'] = ext.get('ddir', '')
        ext['shll'] = ext.get('shll', 'N')=='Y' if str(ext.get('shll', 'N'))    in 'NY'            else ext.get('shll', False)
        ext['prms'] = ext.get('prms', '')
        ext['savs'] = ext.get('savs', SAVS_N)
        ext['rslt'] = ext.get('rslt', RSLT_OP)  if     ext.get('rslt', RSLT_OP) in self.rslt_vals  else RSLT_OP     # def is "to panel"
#       ext['rslt'] = ext.get('rslt', RSLT_N)   if     ext.get('rslt', RSLT_N)  in self.rslt_vals  else RSLT_N
        ext['encd'] = ext.get('encd', '')
        ext['lxrs'] = ext.get('lxrs', '')
        ext['pttn'] = ext.get('pttn', '')
        return ext

    def _calc_umc_vals(self, file_nm=None):
        file_nm         = file_nm   if file_nm is not None else     ed.get_filename()
        (cCrt, rCrt
        ,cEnd, rEnd)    = ed.get_carets()[0]
        umc_vals        = {}            
        for umc in self.umacrs:
            pass;              #LOG and log('umc={}',(umc))
            umc_vals[umc['nm']]  = _subst_fltd_props(umc['ex'], file_nm, cCrt, rCrt, umcs=umc_vals, prjs=get_proj_vars())
#           umc_vals[umc['nm']]  = _subst_props(umc['ex'], file_nm, cCrt, rCrt, umcs=umc_vals, prjs=get_proj_vars())
            pass;              #LOG and log('umc_vals={}',(umc_vals))
        return umc_vals
       #def _calc_umc_vals
       
   #class Command

def _adv_prop(act, ext, par=''):
    core_props  = ('id','nm','file','ddir','shll','prms','savs','rslt','encd','lxrs','pttn','pttn-test', 'jext')
    if False:pass
    elif act=='get-dict':
        return {k:v for k,v in ext.items() 
                    if  k not in core_props}
#   elif act=='apply-json':
#       js  = par
#       for k in [k for k in ext.keys() if k not in core_props]:
#           ext.pop(k, None)
#       adv = json.loads(js)
#       adv = {k:v for k,v in adv.items() 
#                  if  k not in core_props}
#       pass;                  #LOG and log('ext, adv={}',(ext, adv))
#       ext.update(adv)
   #def _adv_prop

def quote(s):
    import urllib.parse
    return urllib.parse.quote(s)
def upper(s):   return s.upper()
def lower(s):   return s.lower()
def title(s):   return s.title()
FILTER_REDUCTS={
    'q':'quote'
,   'u':'upper'
,   'l':'lower'
,   't':'title'
}
def _fltrd_to(mcr_flt, base_val):
    """ Apply filter[s] for
            NM|func1[:par1,par2[|func2]]
        as func2(func1(base_val,par1,par2)) 
    """
    pass;                      #LOG and log('mcr_flt, base_val={}',(mcr_flt, base_val))
    flt_val     = base_val
    func_parts  = mcr_flt.split('|')[1:]
    for func_part in func_parts:
        pass;                  #LOG and log('func_part={}',(func_part))
        func_nm,\
        *params = func_part.split(':')
        pass;                  #LOG and log('flt_val, func_nm, params={}',(flt_val, func_nm, params))
        params  = ','+params[0] if params else ''
        func_nm = FILTER_REDUCTS.get(func_nm, func_nm)
        if '.' in func_nm:
            pass;              #LOG and log('import {}','.'.join(func_nm.split('.')[:-1]))
            importlib.import_module('.'.join(func_nm.split('.')[:-1]))
        pass;                  #LOG and log('eval({})', f('{}({}{})', func_nm, repr(flt_val), params))
        try:
            flt_val = eval(                             f('{}({}{})', func_nm, repr(flt_val), params))
        except Exception as ex:
            flt_val = 'Error: '+str(ex)
       #for func_part
    pass;                      #LOG and log('flt_val={}',(flt_val))
    return str(flt_val)
   #_fltrd_to

def _replace_mcr(prm, mk, mv):
    prm     = prm.replace(mk, mv)
    mkf     = mk[:-1] + '|'
    if mkf in prm:    # Has Filters
        prm = re.sub(re.escape(mkf) + r'[^}]+}'
                    ,lambda match: _fltrd_to(match.group(0).strip('{}'), mv)
                    ,prm)
    return prm
   #_replace_mcr

def _subst_fltd_props(prm, file_nm, cCrt=-1, rCrt=-1, ext_nm='', umcs={}, prjs={}):
    pass;                      #return _subst_props(prm, file_nm, cCrt, rCrt, ext_nm, umcs, prjs)
    pass;                      #LOG and log('prm, file_nm, cCrt=-1, rCrt=-1, ext_nm={}',(prm, file_nm, cCrt, rCrt, ext_nm))
    pass;                      #LOG and log('umcs, prjs={}',(umcs, prjs))
    if '{' not in prm:  return prm
    # Substitude OS environments
    for env_k,env_v in os.environ.items():
        prm     = _replace_mcr(prm, '{OS:'+env_k+'}', env_v)
        if '{' not in prm:  return prm
    
    # Substitude Project vars
    for prj_k,prj_v in prjs.items():
        prm     = _replace_mcr(prm, prj_k, prj_v)
        if '{' not in prm:  return prm

    if '{' not in prm:  return prm
    # Substitude std vars
    app_dir = app.app_path(app.APP_DIR_EXE)
    if      '{AppDir'             in prm: prm = _replace_mcr(prm, '{AppDir}'        ,   app_dir)
    if      '{AppDrive'           in prm: prm = _replace_mcr(prm, '{AppDrive}'      ,   app_dir[0:2] if os.name=='nt' and app_dir[1]==':' else '')
            
    def text2temp(ed_):
        src_fn  = ed_.get_filename()
        if src_fn and not ed_.get_prop(app.PROP_MODIFIED):
            return src_fn
        
        src_stem= '.'.join(os.path.basename(src_fn).split('.')[0:-1])
        src_ext =          os.path.basename(src_fn).split('.')[-1]
        trg_dir = tempfile.gettempdir() + os.sep + 'cudatext'
        if not os.path.isdir(trg_dir):
            os.mkdir(trg_dir)
        trg_fn      = trg_dir + os.sep + src_stem + '.text.'              + src_ext
        uni_nm      = 0
        while os.path.isfile(trg_fn):
            uni_nm += 1
            trg_fn  = trg_dir + os.sep + src_stem + f('.text{}.', uni_nm) + src_ext
            
        open(trg_fn, 'w').write(ed_.get_text_all())
        return trg_fn
       #def text2temp
    
    for gr in range(apx.get_groups_count()):
        sGN         = 'g'+str(gr+1)
        pass;                  #log('sGN,prm,_+sGN+}} in prm={}',(sGN,prm,'_'+sGN+'}' in prm))
        if '_'+sGN+'}' not in prm and \
           '_'+sGN+'|' not in prm:  continue        
        gr_ed       = app.ed_group(gr)
        if not gr_ed:               continue        
        f_gN_nm     = gr_ed.get_filename()
        if not f_gN_nm:             continue        
        if  '{FileName_' +sGN+'}' in prm \
        or  '{FileName_' +sGN+'|' in prm: prm = _replace_mcr(prm, '{FileName_'     +sGN+'}' ,                          f_gN_nm)
        if  '{FileDir_'  +sGN     in prm: prm = _replace_mcr(prm, '{FileDir_'      +sGN+'}' ,          os.path.dirname(f_gN_nm))
        if  '{FileNameOnly_'+sGN  in prm: prm = _replace_mcr(prm, '{FileNameOnly_' +sGN+'}' ,         os.path.basename(f_gN_nm))
        if  '{FileNameNoExt_'+sGN in prm: prm = _replace_mcr(prm, '{FileNameNoExt_'+sGN+'}' ,'.'.join(os.path.basename(f_gN_nm).split('.')[0:-1]))
        if  '{FileExt_'  +sGN     in prm: prm = _replace_mcr(prm, '{FileExt_'      +sGN+'}' ,         os.path.basename(f_gN_nm).split('.')[-1])
        if  '{ContentAsTemp_'+sGN in prm: prm = _replace_mcr(prm, '{ContentAsTemp_'+sGN+'}' ,    text2temp(gr_ed))
        if  '{Lexer_'    +sGN+'}' in prm \
        or  '{Lexer_'    +sGN+'|' in prm: prm = _replace_mcr(prm, '{Lexer_'        +sGN+'}' , gr_ed.get_prop(app.PROP_LEXER_FILE))
    if      '{FileName}'          in prm \
    or      '{FileName|'          in prm: prm = _replace_mcr(prm, '{FileName}'      ,                          file_nm)
    if      '{FileDir'            in prm: prm = _replace_mcr(prm, '{FileDir}'       ,          os.path.dirname(file_nm))
    if      '{FileNameOnly'       in prm: prm = _replace_mcr(prm, '{FileNameOnly}'  ,         os.path.basename(file_nm))
    if      '{FileNameNoExt'      in prm: prm = _replace_mcr(prm, '{FileNameNoExt}' ,'.'.join(os.path.basename(file_nm).split('.')[0:-1]))
    if      '{FileExt'            in prm: prm = _replace_mcr(prm, '{FileExt}'       ,         os.path.basename(file_nm).split('.')[-1])
    if      '{ContentAsTemp'      in prm: prm = _replace_mcr(prm, '{ContentAsTemp}'         ,    text2temp(ed))
    if      '{Lexer}'             in prm \
    or      '{Lexer|'             in prm: prm = _replace_mcr(prm, '{Lexer}'         ,    ed.get_prop(app.PROP_LEXER_FILE))
    if      '{LexerAtCaret'       in prm: prm = _replace_mcr(prm, '{LexerAtCaret}'  ,    ed.get_prop(app.PROP_LEXER_CARET))

    if rCrt!=-1:
        if  '{CurrentLine}'       in prm \
        or  '{CurrentLine|'       in prm: prm = _replace_mcr(prm, '{CurrentLine}'       , ed.get_text_line(rCrt))
        if  '{CurrentLineNum}'    in prm \
        or  '{CurrentLineNum|'    in prm: prm = _replace_mcr(prm, '{CurrentLineNum}'    , str(1+rCrt))
        if  '{CurrentLineNum0'    in prm: prm = _replace_mcr(prm, '{CurrentLineNum0}'   , str(  rCrt))
        if  '{CurrentColumnNum}'  in prm \
        or  '{CurrentColumnNum|'  in prm: prm = _replace_mcr(prm, '{CurrentColumnNum}'  , str(1+ed.convert(app.CONVERT_CHAR_TO_COL, cCrt, rCrt)[0]))
        if  '{CurrentColumnNum0'  in prm: prm = _replace_mcr(prm, '{CurrentColumnNum0}' , str(  ed.convert(app.CONVERT_CHAR_TO_COL, cCrt, rCrt)[0]))
        if  '{SelectedText'       in prm: prm = _replace_mcr(prm, '{SelectedText}'      ,       ed.get_text_sel())
        if  '{CurrentWord'        in prm: prm = _replace_mcr(prm, '{CurrentWord}'       , get_current_word(ed, cCrt, rCrt))

    if '{Interactive}' in prm \
    or '{Interactive|' in prm:
        ans = app.dlg_input('Param for call {}'.format(ext_nm), '')
        if ans is None: return
        prm = _replace_mcr(prm, '{Interactive}'     , ans)
    if '{InteractiveFile' in prm:
        ans = app.dlg_file(True, '!', '', '')   # '!' to disable check "filename exists"
        if ans is None: return
        prm = _replace_mcr(prm, '{InteractiveFile}' , ans)

    if '{' not in prm:  return prm
    # Substitude user vars
    for umc_k,umc_v in umcs.items():
        prm     = _replace_mcr(prm, umc_k, umc_v)
        if '{' not in prm:  return prm
    
    return prm
   #_subst_fltd_props

#def _subst_props(prm, file_nm, cCrt=-1, rCrt=-1, ext_nm='', umcs={}, prjs={}):
#   pass;                      #LOG and log('prm, file_nm, cCrt=-1, rCrt=-1, ext_nm={}',(prm, file_nm, cCrt, rCrt, ext_nm))
#   pass;                       LOG and log('umcs, prjs={}',(umcs, prjs))
#   if '{' not in prm:  return prm
#   # Substitude Project vars
#   for prj_k,prj_v in prjs.items():
#       prm = prm.replace(prj_k, prj_v)
#       if '{' not in prm:  return prm
#
#   if '{' not in prm:  return prm
#   # Substitude std vars
#   app_dir = app.app_path(app.APP_DIR_EXE)
#   if      '{AppDir}'            in prm: prm = prm.replace('{AppDir}'       ,   app_dir)
#   if      '{AppDrive}'          in prm: prm = prm.replace('{AppDrive}'     ,   app_dir[0:2] if os.name=='nt' and app_dir[1]==':' else '')
#           
#   if      '{FileName}'          in prm: prm = prm.replace('{FileName}'     ,                          file_nm)
#   if      '{FileDir}'           in prm: prm = prm.replace('{FileDir}'      ,          os.path.dirname(file_nm))
#   if      '{FileNameOnly}'      in prm: prm = prm.replace('{FileNameOnly}' ,         os.path.basename(file_nm))
#   if      '{FileNameNoExt}'     in prm: prm = prm.replace('{FileNameNoExt}','.'.join(os.path.basename(file_nm).split('.')[0:-1]))
#   if      '{FileExt}'           in prm: prm = prm.replace('{FileExt}'      ,         os.path.basename(file_nm).split('.')[-1])
#   if      '{Lexer}'             in prm: prm = prm.replace('{Lexer}'        ,    ed.get_prop(app.PROP_LEXER_FILE))
#   if      '{LexerAtCaret}'      in prm: prm = prm.replace('{LexerAtCaret}' ,    ed.get_prop(app.PROP_LEXER_CARET))
#
#   if rCrt!=-1:
#       if  '{CurrentLine}'       in prm: prm = prm.replace('{CurrentLine}'     , ed.get_text_line(rCrt))
#       if  '{CurrentLineNum}'    in prm: prm = prm.replace('{CurrentLineNum}'  , str(1+rCrt))
#       if  '{CurrentLineNum0}'   in prm: prm = prm.replace('{CurrentLineNum0}' , str(  rCrt))
#       if  '{CurrentColumnNum}'  in prm: prm = prm.replace('{CurrentColumnNum}', str(1+ed.convert(app.CONVERT_CHAR_TO_COL, cCrt, rCrt)[0]))
#       if  '{CurrentColumnNum0}' in prm: prm = prm.replace('{CurrentColumnNum0}',str(  ed.convert(app.CONVERT_CHAR_TO_COL, cCrt, rCrt)[0]))
#       if  '{SelectedText}'      in prm: prm = prm.replace('{SelectedText}'    , ed.get_text_sel())
#       if  '{CurrentWord}'       in prm: prm = prm.replace('{CurrentWord}'     , get_current_word(ed, cCrt, rCrt))
#
#   if '{Interactive}' in prm:
#       ans = app.dlg_input('Param for call {}'.format(ext_nm), '')
#       if ans is None: return
#       prm = prm.replace('{Interactive}'     , ans)
#   if '{InteractiveFile}' in prm:
#       ans = app.dlg_file(True, '!', '', '')   # '!' to disable check "filename exists"
#       if ans is None: return
#       prm = prm.replace('{InteractiveFile}' , ans)
#       
#   if '{' not in prm:  return prm
#   # Substitude user vars
#   for umc_k,umc_v in umcs.items():
#       prm = prm.replace(umc_k, umc_v)
#       if '{' not in prm:  return prm
#       
#   return prm
#  #def _subst_props

def get_current_word(ed, c_crt, r_crt):
    sel_text    = ed.get_text_sel()
    if sel_text:    return sel_text;
    wrdchs      = apx.get_opt('word_chars', '') + '_'
    wrdcs_re    = re.compile(r'^[\w'+re.escape(wrdchs)+']+')
    line        = ed.get_text_line(r_crt)
    c_crt       = max(0, min(c_crt, len(line)-1))
    c_bfr       = line[c_crt-1] if c_crt>0         else ' '
    c_aft       = line[c_crt]   if c_crt<len(line) else ' '
    gp_aft_l    = 0
    gp_bfr_l    = 0
    if (c_bfr.isalnum() or c_bfr in wrdchs):   # abc|
        tx_bfr  = line[:c_crt]
        tx_bfr_r= ''.join(reversed(tx_bfr))
        gp_bfr_l= len(wrdcs_re.search(tx_bfr_r).group())
    if (c_aft.isalnum() or c_aft in wrdchs):   # |abc
        tx_aft  = line[ c_crt:]
        gp_aft_l= len(wrdcs_re.search(tx_aft  ).group())
    pass;              #LOG and log('gp_bfr_l,gp_aft_l={}',(gp_bfr_l,gp_aft_l))
    return line[c_crt-gp_bfr_l:c_crt+gp_aft_l]
   #def get_current_word

def append_prmt(tostr, umacrs, excl_umc=None):
    prms_l  =['{}\t{}'.format(umc['nm'], umc['ex']) 
                for umc in umacrs 
                if (excl_umc is None or umc['nm']!=excl_umc)]
    prms_l +=[pj_k+'\t'+pj_v 
                for pj_k, pj_v in get_proj_vars().items()]
    pass;                      #LOG and log('prms_l={}',(prms_l))
    prms_l +=([]
            +[_('{AppDir}\tDirectory with app executable')]
            +[_('{AppDrive}\t(Win only) Disk of app executable, eg "C:"')]
            +[_('{FileName}\tFull path')]
            +[_('{FileDir}\tFolder path, without file name')]
            +[_('{FileNameOnly}\tFile name only, without folder path')]
            +[_('{FileNameNoExt}\tFile name without extension and path')]
            +[_('{FileExt}\tExtension')]
            +[_('{ContentAsTemp}\tName of [temporary] file with current text')]
            +[_('{Lexer}\tFile lexer')]
            +[_('{LexerAtCaret}\tLocal lexer (at 1st caret)')]
            +[_('{CurrentLine}\tText of current line')]
            +[_('{CurrentLineNum}\tNumber of current line')]
            +[_('{CurrentLineNum0}\tNumber of current line (0-based)')]
            +[_('{CurrentColumnNum}\tNumber of current column')]
            +[_('{CurrentColumnNum0}\tNumber of current column (0-based)')]
            +[_('{SelectedText}\tText')]
            +[_('{CurrentWord}\tText')]
            +[_('{Interactive}\tText will be asked at each running')]
            +[_('{InteractiveFile}\tFile name will be asked')]
            +[f(_('{{FileName_g{0}}}\tFull path of current file in group {0}')                                  , gr+1) for gr in range(6)]
            +[f(_('{{FileDir_g{0}}}\tFolder path, without file name, of current file in group {0}')             , gr+1) for gr in range(6)]
            +[f(_('{{FileNameOnly_g{0}}}\tFile name only, without folder path, of current file in group {0}')   , gr+1) for gr in range(6)]
            +[f(_('{{FileNameNoExt_g{0}}}\tFile name without extension and path of current file in group {0}')  , gr+1) for gr in range(6)]
            +[f(_('{{FileExt_g{0}}}\tExtension of current file in group {0}')                                   , gr+1) for gr in range(6)]
            +[f(_('{{ContentAsTemp_g{0}}}\tName of [temporary] file with current text in group {0}')            , gr+1) for gr in range(6)]
            +[f(_('{{Lexer_g{0}}}\tLexer of current file in group {0}')                                         , gr+1) for gr in range(6)]
             )
    prms_l +=['{OS:'+env_k+'}\t'+env_v 
                for env_k, env_v in os.environ.items()]
                        
    prm_i   = app.dlg_menu(app.MENU_LIST_ALT, '\n'.join(prms_l), caption=_('Variables'))
    if prm_i is not None:
        tostr  = (tostr + (' '+prms_l[prm_i].split('\t')[0])).lstrip()
    return tostr
   #def append_prmt

def _gen_id(ids):
    id4ext      = random.randint(100000, 999999)
    while id4ext in ids:
        id4ext  = random.randint(100000, 999999)
    return id4ext

def get_usage_names():
    return [
        RSLT_NO
    ,   RSLT_TO_PANEL
    ,   RSLT_TO_PANEL_AP
    ,   RSLT_TO_NEWDOC
    ,   RSLT_TO_CLIP
    ,   RSLT_REPL_SEL
    ]
   #def get_usage_names

def get_keys_desc(mdl_mth, id, keys=None):
    if keys is None:
        keys_json   = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'keys.json'
        keys        = apx._json_loads(open(keys_json).read()) if os.path.exists(keys_json) else {}

    cmd_id  = '{},{}'.format(mdl_mth, id)
    cmd_keys= keys.get(cmd_id, {})
    desc    = '/'.join([' * '.join(cmd_keys.get('s1', []))
                       ,' * '.join(cmd_keys.get('s2', []))
                       ]).strip('/')
    return desc
   #def get_keys_desc

def _file_open(op_file):
    if not app.file_open(op_file):
        return None
    for h in app.ed_handles(): 
        op_ed   = app.Editor(h)
        if os.path.samefile(op_file, op_ed.get_filename()):
            return op_ed
    return None
   #def _file_open

#def _get_lexers():
#   lxrs_l  = app.lexer_proc(app.LEXER_GET_LIST, '').splitlines()
#   lxrs_l  = [lxr for lxr in lxrs_l if app.lexer_proc(app.LEXER_GET_ENABLED, lxr)]
#   lxrs_l += ['(none)']
#   return lxrs_l
   #def _get_lexers

def log_status(msg):
    print(msg)
    app.msg_status(msg)
   #def log_status
    
#if __name__ == '__main__' :     # Tests
def _testing():
    Command()._dlg_pattern('', '', 'ext')
#_testing()
        
'''
ToDo
[-][kv-kv][09dec15] Run test cmd
[+][kv-kv][11jan16] Parse output with re
[?][kv-kv][11jan16] Use PROC_SET_ESCAPE
[+][kv-kv][19jan16] Use control top with sys.platform
[?][kv-kv][19jan16] Opt for auto-to-first_rslt
[?][kv-kv][19mar16] wrapper: cals l=r-w
[ ][kv-kv][11apr16] Restore keys if Cancel
[ ][at-kv][01oct16] Moved tool format: in zip, in data\tools
[ ][kv-kv][29oct16] Add mode: Show curr-val / Show macro-val
'''
