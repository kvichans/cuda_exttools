''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '1.2.0 2016-03-12'
ToDo: (see end of file)
'''

import  os, json, random, subprocess, shlex, copy, collections, re, zlib, sys, gettext
import  cudatext        as app
from    cudatext    import ed
import  cudatext_cmd    as cmds
import  cudax_lib       as apx
from    cudax_lib   import log
from    .encodings  import *

THIS    = 'cuda_exttools'
TRIS_DIR= app.app_path(app.APP_DIR_EXE)+'/py/{0}/'.format(THIS)

# Localization
_       = lambda x: x
lng     = app.app_proc(app.PROC_GET_LANG, '')
lng_mo  = TRIS_DIR+'/lang/{}/LC_MESSAGES/{}.mo'.format(lng, THIS)
if os.path.isfile(lng_mo):
    os.environ['LANGUAGE'] = lng
    t   = gettext.translation(THIS, TRIS_DIR+'/lang', languages=[lng])
    _   = t.gettext
    t.install()

pass;                           # Logging
pass;                           LOG = (-2==-2)  # Do or dont logging.
c10,c13,l= chr(10),chr(13),chr(13)

JSON_FORMAT_VER = '20151209'
EXTS_JSON       = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'exttools.json'
#PRESET_JSON     = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'exttools-preset.json'

DTLS_MVUP_H     = _('Move current tool to upper position')
DTLS_MVDN_H     = _('Move current tool to lower position')
DTLS_MNLX_H     = _('For call by command "Run lexer main tool"')
DTLS_CUST_H     = _('Change this dialog sizes')

EXT_HELP_CAP    = _('Tool macros')
EXT_HELP_BODY   = _(
'''In tool properties
   File name
   Parameters
   Initial folder
the following macros are processed.
- Application macros:
   {AppDir}           - Directory with app executable
   {AppDrive}         - (Win only) Disk of app executable, eg "C:"
- Currently focused file macros:
   {FileName}         - Full path
   {FileDir}          - Folder path, without file name
   {FileNameOnly}     - Name only, without folder path
   {FileNameNoExt}    - Name without extension and path
   {FileExt}          - Extension
- Currently focused editor macros (for top caret):
   {CurrentLine}      - text
   {CurrentLineNum}   - number
   {CurrentLineNum0}  - number
   {CurrentColumnNum} - number
   {CurrentColumnNum0}- number
   {SelectedText}     - text 
- Prompted macros:
   {Interactive}      - Text will be asked at each running
   {InteractiveFile}  - File name will be asked''').replace('\t', chr(2)).replace('\r\n','\n').replace('\r','\n').replace('\n','\t')

ADV_PROPS       = [ {'key':'source_tab_as_blanks'
                    ,'cap':'Consider TAB as "N spaces" to interpret output column'
                   #,'cap':'Output column numbers are counted with replace TAB with N spaces'
                    ,'hnt':'Set 8 for a Tool likes "tidy"'
                    ,'def':''
                    }
                 #, {'key':'smth'
                   #,'cap':'Smth'
                   #,'hnt':'s m t h'
                   #,'def':''
                   #}
                  ]

RSLT_NO         = _('Ignore')
RSLT_TO_PANEL   = _('Output panel')
RSLT_TO_PANEL_AP= _('Output panel (append)')
RSLT_TO_NEWDOC  = _('Copy to new document')
RSLT_TO_CLIP    = _('Copy to clipboard')
RSLT_REPL_SEL   = _('Replace selection')
RSLT_N          = 'N'
RSLT_OP         = 'OP'
RSLT_OPA        = 'OPA'
RSLT_ND         = 'ND'
RSLT_CB         = 'CB'
RSLT_SEL        = 'SEL'

SAVS_NOTHING    = _('Nothing')
SAVS_ONLY_CUR   = _('Current document')
SAVS_ALL_DOCS   = _('All documents')
SAVS_N          = 'N'
SAVS_Y          = 'Y'
SAVS_A          = 'A'

FROM_API_VERSION= '1.0.120' # dlg_custom: type=linklabel, hint
def F(s, *args, **kwargs):return s.format(*args, **kwargs)
C1      = chr(1)
C2      = chr(2)
POS_FMT = 'pos={l},{t},{r},{b}'.format
POS_LTR = 'pos={l},{t},{r},0'.format
def POS_TLW(t=0,l=0,w=0):   return POS_LTR(l=l, t=t, r=l+w)
def cust_it(tp, **kw):
    tp      = {'check-bt':'checkbutton'}.get(tp, tp)
    lst     = ['type='+tp]
    lst    += [POS_TLW(t=kw['t'],l=kw['l'],w=kw['w'])
                if 'w'     in kw else
               POS_LTR(l=kw['l'],t=kw['t'],r=kw['r'])
                if 'b' not in kw else
               POS_FMT(l=kw['l'],t=kw['t'],r=kw['r'],b=kw['b'])
              ]
    for k in ['cap', 'hint', 'props', 'en']:
        if k in kw:
            lst += [k+'='+str(kw[k])]
    if 'items' in kw:
        lst+= ['items='+'\t'.join(kw['items'])]
    if 'val' in kw:
        val = kw['val']
        val = '\t'.join(val) if isinstance(val, list) else val
        lst+= ['val='+str(val)]
    pass;                      #LOG and log('lst={}',lst)
    return C1.join(lst)
   #def cust_it
GAP     = 5
def top_plus_for_os(what_control, base_control='edit'):
    ''' Addition for what_top to align text with base.
        Params
            what_control    'check'/'label'/'edit'/'button'/'combo'/'combo_ro'
            base_control    'check'/'label'/'edit'/'button'/'combo'/'combo_ro'
    '''
    if what_control==base_control:
        return 0
    env = sys.platform
    if base_control=='edit': 
        if env=='win32':
            return apx.icase(what_control=='check',    1
                            ,what_control=='label',    3
                            ,what_control=='button',  -1
                            ,what_control=='combo_ro',-1
                            ,what_control=='combo',    0
                            ,True,                     0)
        if env=='linux':
            return apx.icase(what_control=='check',    1
                            ,what_control=='label',    5
                            ,what_control=='button',   1
                            ,what_control=='combo_ro', 0
                            ,what_control=='combo',   -1
                            ,True,                     0)
        if env=='darwin':
            return apx.icase(what_control=='check',    2
                            ,what_control=='label',    3
                            ,what_control=='button',   0
                            ,what_control=='combo_ro', 1
                            ,what_control=='combo',    0
                            ,True,                     0)
        return 0
       #if base_control=='edit'
    return top_plus_for_os(what_control, 'edit') - top_plus_for_os(base_control, 'edit')
   #def top_plus_for_os

at4chk  = top_plus_for_os('check')
at4lbl  = top_plus_for_os('label')
at4btn  = top_plus_for_os('button')
at4cbo  = top_plus_for_os('combo_ro')

class Command:
    def __init__(self):
        # Static data
        self.savs_caps  = [SAVS_NOTHING, SAVS_ONLY_CUR, SAVS_ALL_DOCS]
        self.savs_vals  = [SAVS_N,       SAVS_Y,        SAVS_A]
        self.savs_v2c   = {SAVS_N:SAVS_NOTHING
                          ,SAVS_Y:SAVS_ONLY_CUR
                          ,SAVS_A:SAVS_ALL_DOCS}
        self.rslt_caps  = [RSLT_NO, RSLT_TO_PANEL, RSLT_TO_PANEL_AP, RSLT_TO_NEWDOC, RSLT_TO_CLIP, RSLT_REPL_SEL]
        self.rslt_vals  = [RSLT_N,  RSLT_OP,       RSLT_OPA,         RSLT_ND,        RSLT_CB,      RSLT_SEL]
        self.rslt_v2c   = {RSLT_N:RSLT_NO
                          ,RSLT_OP:RSLT_TO_PANEL
                          ,RSLT_OPA:RSLT_TO_PANEL_AP
                          ,RSLT_ND:RSLT_TO_NEWDOC
                          ,RSLT_CB:RSLT_TO_CLIP
                          ,RSLT_SEL:RSLT_REPL_SEL}

        # Saving data
        self.saving      = apx._json_loads(open(EXTS_JSON).read()) if os.path.exists(EXTS_JSON) else {
                             'ver':JSON_FORMAT_VER
                            ,'list':[]
                            ,'dlg_prs':{}
                            ,'ext4lxr':{}
                            ,'preset':[]
                            }
        if self.saving.setdefault('ver', '') < JSON_FORMAT_VER:
            # Adapt to new format
            pass
        self.dlg_prs    = self.saving.setdefault('dlg_prs', {})
        self.ext4lxr    = self.saving.setdefault('ext4lxr', {})
        self.preset     = self.saving.setdefault('preset', [])
        self.exts       = self.saving['list']
            
        # Runtime data
        self.ext4id     = {str(ext['id']):ext for ext in self.exts}
#       self.id2crc     = {}
        self.crcs       = {}
        self.last_crc   = -1
        self.last_ext_id= 0
#       self.last_run_id= -1
        self.last_op_ind= -1

        # Adjust
        for ext in self.exts:
            self._fill_ext(ext)

        # Actualize lexer-tool 
        lxrs_l  = _get_lexers()
        for i_lxr in range(len(self.ext4lxr)-1,-1,-1):
            lxr = list(self.ext4lxr.keys())[i_lxr]
            if lxr                    not in lxrs_l \
            or str(self.ext4lxr[lxr]) not in self.ext4id:
                del self.ext4lxr[lxr]
        pass;                  #LOG and log('self.preset={}',self.preset)
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
            if app.app_exe_version() >= '1.0.131':
                plg_ind = [i for (i,nm) in enumerate(top_nms) if '|plugins' in nm][0]     ##?? 
            else: # old, pre i18n
                plg_ind = top_nms.index('&Plugins|')                                                    ##?? 
            id_menu = app.app_proc( app.PROC_MENU_ADD, '{};{};{};{}'.format('top', 0, _('&Tools'), 1+plg_ind))
            ed.exttools_id_menu = id_menu               ##?? dirty hack!

        # Fill
        app.app_proc(app.PROC_MENU_ADD, '{};cuda_exttools,dlg_config;{}'.format(    id_menu,    _('Con&fig...')))
        app.app_proc(app.PROC_MENU_ADD, '{};cuda_exttools,run_lxr_main;{}'.format(  id_menu,    _('R&un lexer main tool')))
        id_rslt = app.app_proc( app.PROC_MENU_ADD, '{};{};{}'.format(               id_menu, 0, _('Resul&ts')))
        app.app_proc(app.PROC_MENU_ADD, '{};cuda_exttools,show_next_result;{}'.format(id_rslt,  _('Nex&t tool result')))
        app.app_proc(app.PROC_MENU_ADD, '{};cuda_exttools,show_prev_result;{}'.format(id_rslt,  _('&Previous tool result')))
        if 0==len(self.exts):
            return
        app.app_proc(app.PROC_MENU_ADD, '{};;-'.format(id_menu))
        for ext in self.exts:
            app.app_proc(app.PROC_MENU_ADD, '{};cuda_exttools,run,{};{}'.format(id_menu, ext['id'], ext['nm']))
       #def _adapt_menu
        
    def _do_acts(self, what='', acts='|save|second|reg|keys|menu|'):
        ''' Use exts list '''
        pass;                  #LOG and log('what, acts={}',(what, acts))
        # Save
        if '|save|' in acts:
            open(EXTS_JSON, 'w').write(json.dumps(self.saving, indent=4))
        
        # Secondary data
        if '|second|' in acts:
            self.ext4id     = {str(ext['id']):ext for ext in self.exts}
        
        # Register new subcommands
        if '|reg|' in acts:
            reg_subs        = 'cuda_exttools;run;{}'.format('\n'.join(
                             'Tools: {}\t{}'.format(ext['nm'],ext['id']) 
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

    def run_lxr_main(self):
        lxr     = ed.get_prop(app.PROP_LEXER_FILE)
        if lxr not in self.ext4lxr:
            return app.msg_status('No main tool for lexer "{}"'.format(lxr))
        self.run(self.ext4lxr[lxr])
       #def run_lxr_main

    def run(self, ext_id):
        ''' Main (and single) way to run any exttool
        '''
        self.last_ext_id = ext_id
        ext_id  = str(ext_id)
        pass;                  #LOG and log('ext_id={}',ext_id)
        ext     = self.ext4id.get(str(ext_id))
        if ext is None:
            return app.msg_status('No Tool: {}'.format(ext_id))
        nm      = ext['nm']
        lxrs    = ext['lxrs']
        lxr_cur = ed.get_prop(app.PROP_LEXER_FILE)
        lxr_cur = lxr_cur if lxr_cur else '(none)' 
        pass;                  #LOG and log('nm="{}", lxr_cur="{}", lxrs="{}"',nm, lxr_cur, lxrs)
        if (lxrs
        and not (','+lxr_cur+',' in ','+lxrs+',')):
            return app.msg_status(_('Tool "{}" is not suitable for lexer "{}". It works only with "{}"').format(nm, lxr_cur, lxrs))
        
#       self.last_run_id = ext_id
        cmnd    = ext['file']
        prms_s  = ext['prms']
        ddir    = ext['ddir']
        pass;                  #LOG and log('nm="{}", cmnd="{}", ddir="{}", prms_s="{}"',nm, cmnd, ddir, prms_s)
        
        # Saving
        if SAVS_Y==ext.get('savs', SAVS_N):
            if not app.file_save():  return
        if SAVS_A==ext.get('savs', SAVS_N):
            ed.cmd(cmds.cmd_FileSaveAll)
        
        # Preparing
        file_nm = ed.get_filename()
        (cCrt, rCrt
        ,cEnd, rEnd)    = ed.get_carets()[0]
        prms_l  = shlex.split(prms_s)
        for ind, prm in enumerate(prms_l):
            prm_raw = prm
            prm     = subst_props(prm, file_nm, cCrt, rCrt, ext['nm'])
            if prm_raw != prm:
                prms_l[ind] = prm
#               prms_l[ind] = shlex.quote(prm)
           #for ind, prm
        cmnd        = subst_props(cmnd, file_nm, cCrt, rCrt, ext['nm'])
        ddir        = subst_props(ddir, file_nm, cCrt, rCrt, ext['nm'])

        pass;                  #LOG and log('ready prms_l={}',(prms_l))

        val4call= [cmnd] + prms_l
        pass;                  #LOG and log('val4call={}',(val4call))

        # Calling
        rslt    = ext.get('rslt', RSLT_N)
        nmargs  = {'cwd':ddir} if ddir else {}
        if RSLT_N==rslt:
            # Without capture
            try:
                subprocess.Popen(val4call, **nmargs)
            except Exception as ex:
                app.msg_box('{}: {}'.format(type(ex).__name__, ex), app.MB_ICONWARNING)
                pass;           LOG and log('fail Popen',)
            return
        
        # With capture
        pass;                  #LOG and log("'Y'==ext.get('shll', 'N')",'Y'==ext.get('shll', 'N'))
        nmargs['stdout']=subprocess.PIPE
        nmargs['stderr']=subprocess.STDOUT
        nmargs['shell'] =ext.get('shll', False)
        pass;                  #LOG and log('?? Popen nmargs={}',nmargs)
        try:
            pipe    = subprocess.Popen(val4call, **nmargs)
        except Exception as ex:
            app.msg_box('{}: {}'.format(type(ex).__name__, ex), app.MB_ICONWARNING)
            pass;               LOG and log('fail Popen',)
            return
        if pipe is None:
            pass;               LOG and log('fail Popen',)
            app.msg_status('Fail call: {} {}'.format(cmnd, prms_s))
            return
        pass;                  #LOG and log('ok Popen',)
        app.msg_status('Call: {} {}'.format(cmnd, prms_s))

        rslt_txt= ''
        crc_tag = 0
        def gen_save_crc(ext, cwd='', filepath='', filecol=0, filerow=0):
            ''' Generate 32-bit int for each ext running '''
            text    = '|'.join([str(ext[k]) for k in ext]
                              +[F('{}|{}|{}|{}|{}', cwd, filepath, cCrt, rCrt, len(self.crcs))]
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
            app.app_log(app.LOG_SET_PANEL, app.LOG_PANEL_OUTPUT)
            ed.focus()
            if rslt==RSLT_OP:
                app.app_log(app.LOG_CLEAR, '')
#               self.last_op_ind = -1
#               crc     = self.id2crc[ext['id']]
            else: # rslt==RSLT_OPA
                pass
#               self.id2crc[ext['id']] += 1         # For separate serial runnings of same tool
#               crc     = self.id2crc[ext['id']]
        elif rslt ==  RSLT_ND:
            app.file_open('')

        while True:
            out_ln = pipe.stdout.readline().decode(ext.get('encd', 'utf-8'))
            if 0==len(out_ln): break
            out_ln = out_ln.strip('\r\n')
            pass;              #LOG and log('out_ln={}',out_ln)
            if False:pass
            elif rslt in (RSLT_OP, RSLT_OPA):
                app.app_log(app.LOG_ADD, out_ln, crc_tag)
            elif rslt ==  RSLT_ND:
                ed.set_text_line(-1, out_ln)
            elif rslt in (RSLT_CB, RSLT_SEL):
                rslt_txt+= out_ln + '\n'
           #while True

        rslt_txt= rslt_txt.strip('\n')
        if False:pass
        elif rslt == RSLT_CB:
            app.app_proc(app.PROC_SET_CLIP, rslt_txt)
        elif rslt == RSLT_SEL:
            crts    = ed.get_carets()
            for (cCrt, rCrt, cEnd, rEnd) in crts.reverse():
                if -1!=cEnd:
                    (rCrt, cCrt), (rEnd, cEnd) = apx.minmax((rCrt, cCrt), (rEnd, cEnd))
                    ed.delete(cCrt, rCrt, cEnd, rEnd)
                ed.insert(cCrt, rCrt, rslt_txt)
        elif rslt in (RSLT_OP, RSLT_OPA):
            ed.focus()
       #def run
       
    def on_output_nav(self, ed_self, output_line, crc_tag):
        pass;                  #LOG and log('output_line, crc_tag={}',(output_line, crc_tag))
#       ext_lst = [ext for ext in self.exts if self.id2crc[ext['id']]==crc_tag]
#       if not ext_lst:                 return app.msg_status('No Tool to parse output line')
#       ext     = ext_lst[0]
        
        crc_inf = self.crcs.get(crc_tag, {})
        ext     = crc_inf.get('ext')
        if not ext:                         app.msg_status(_('No Tool to parse the output line'));return
        if not ext['pttn']:                 app.msg_status(_('Tool "{}" has not Pattern property').format(ext['nm']));return
        pttn    = ext['pttn']
        grp_dic = re.search(pttn, output_line).groupdict('') if re.search(pttn, output_line) is not None else {}
        if not grp_dic or not (
            'line'  in grp_dic 
        or  'line0' in grp_dic):            app.msg_status(_('Tool "{}" could not find a line-number into output line').format(ext['nm']));return # '
        nav_file=     grp_dic.get('file' , crc_inf['pth']  )
        nav_line= int(grp_dic.get('line' , 1+int(grp_dic.get('line0', 0))))-1
        nav_col = int(grp_dic.get('col'  , 1+int(grp_dic.get('col0' , 0))))-1
#       nav_lin0= int(grp_dic.get('line0', 0))
#       nav_col0= int(grp_dic.get('col0' , 0))
#       nav_line= nav_lin0 if 'line' not in grp_dic  and 'line0' in grp_dic else nav_line
#       nav_col = nav_col0 if 'col'  not in grp_dic  and 'col0'  in grp_dic else nav_col
        pass;                  #LOG and log('nav_file, nav_line, nav_col={}',(nav_file, nav_line, nav_col))
#       nav_file= crc_inf['file'] \
#                   if not nav_file else 
#                 nav_file
        bs_dir  = ext['ddir']
        bs_dir  = os.path.dirname(crc_inf['pth']) \
                    if not bs_dir else  \
                  subst_props(bs_dir, crc_inf['pth'])
        nav_file= os.path.join(bs_dir, nav_file)
        pass;                  #LOG and log('nav_file={}',(nav_file))
        if not os.path.exists(nav_file):    app.msg_status(_('Cannot open: {}').format(nav_file));return
        
        app.app_log(app.LOG_SET_PANEL, app.LOG_PANEL_OUTPUT)
        self.last_op_ind = app.app_log(app. LOG_GET_LINEINDEX, '')
        
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
#       if str(self.last_run_id) not in self.ext4id:
#           return app.msg_status('No Tool for navigation')

        crc_inf     = self.crcs.get(self.last_crc, {})
        ext         = crc_inf.get('ext')
#       ext         = self.ext4id[str(self.last_run_id)]
#       ext_crc     = self.id2crc[ext['id']]
        ext_pttn    = ext['pttn']
        app.app_log(app.LOG_SET_PANEL, app.LOG_PANEL_OUTPUT)
        op_line_tags=app.app_log(app.LOG_GET_LINES, '')
        pass;                  #LOG and log('op_line_tags={}',op_line_tags)
        op_line_tags=[(item.split(c13)[0], int(item.split(c13)[1])) 
                        if c13 in item else 
                      (item, 0)
                        for item in op_line_tags.split(c10)]
        pass;                  #LOG and log('op_line_tags={}',op_line_tags)
        for op_ind in (range(self.last_op_ind+1, len(op_line_tags)) 
                        if what=='next' else
                       range(self.last_op_ind-1, -1, -1) 
                      ):
            line, crc   = op_line_tags[op_ind]
            if crc != self.last_crc:            continue    #for
            if not re.search(ext_pttn, line):   continue    #for
            self.last_op_ind = op_ind
            app.app_log(app.LOG_SET_PANEL, app.LOG_PANEL_OUTPUT)
            app.app_log(app. LOG_SET_LINEINDEX, str(op_ind))
            self.on_output_nav(ed, line, crc)
            break   #for
        else:#for
            app.msg_status('No more results for navigation')
       #def _show_result
       
    def dlg_config(self):
        return self._dlg_config_list()
    def _dlg_config_list(self):
        if app.app_api_version()<FROM_API_VERSION:  return app.msg_status(_('Need update CudaText'))

        keys_json   = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'keys.json'
        keys        = apx._json_loads(open(keys_json).read()) if os.path.exists(keys_json) else {}
        
        ids     = [ext['id'] for ext in self.exts]
        ext_ind = ids.index(self.last_ext_id) if self.last_ext_id in ids else min(0, len(ids)-1)

        GAP2    = GAP*2    
        prs     = self.dlg_prs
        pass;                  #LOG and log('prs={}',prs)
        while True:
            ext_nz_d        = collections.OrderedDict([
                           ('Name'              ,prs.get('nm'  , '150'))
                          ,('Keys'              ,prs.get('keys', '100'))
                          ,('File | >shell cmd' ,prs.get('file', '180'))
                          ,('Params'            ,prs.get('prms', '100'))
                          ,('Folder'            ,prs.get('ddir', '100'))
                          ,('Lexers'            ,prs.get('lxrs', 'C50'))
                          ,('Capture'           ,prs.get('rslt', 'C50'))
                          ,('Saving'            ,prs.get('savs', 'C30'))
                          ])
            ACTS_W          = prs.get('w_btn', 90)
            WD_LST, HT_LST  = (sum([int(w.lstrip('LRC')) for w in ext_nz_d.values() if w[0]!='-'])+len(ext_nz_d)+10
                              ,prs.get('h_list', 300))
            ACTS_T          = [GAP2+HT_LST  + GAP*ind+25*(ind-1)     for ind in range(20)]
            ACTS_L          = [GAP+         + GAP*ind+ACTS_W*(ind-1) for ind in range(20)]
            WD_LST_MIN      = GAP*10+ACTS_W*8
            if WD_LST < WD_LST_MIN:
                ext_nz_d['Name']    = str(WD_LST_MIN-WD_LST + int(ext_nz_d['Name']))
                WD_LST              = WD_LST_MIN
            DLG_W, DLG_H    = max(WD_LST, ACTS_L[9])+GAP*4, ACTS_T[3]#+GAP
            ext_hnzs    = ['{}={}'.format(nm, '0' if sz[0]=='-' else sz) for (nm,sz) in ext_nz_d.items()]
            ext_vlss    = []
            for ext in self.exts:
                ext_vlss+=[[                                    ext['nm']
                          ,get_keys_desc('cuda_exttools,run',   ext['id'], keys)
                          ,('>' if                              ext['shll'] else '')
                          +                                     ext['file']
                          ,                                     ext['prms']
                          ,                                     ext['ddir']
                          ,                                     ext['lxrs']
                          ,                                     ext['rslt']
                          ,                                     ext['savs']
                          ]]
            pass;              #LOG and log('ext_hnzs={}',ext_hnzs)
            pass;              #LOG and log('ext_vlss={}',ext_vlss)

            ids     = [ext['id'] for ext in self.exts]
            ext     = self.exts[ext_ind] if ext_ind in range(len(self.exts)) else None
            pass;              #LOG and log('ext_ind, ext={}',(ext_ind, ext))
            
            itms    = ['\r'.join(ext_hnzs)] \
                    + [' \r'.join(ext_vls) for ext_vls in ext_vlss]
            ans = app.dlg_custom('Tools'   ,DLG_W, DLG_H, '\n'.join([]
            #LIST
 +[cust_it(tp='label'   ,t=GAP      ,l=GAP      ,r=GAP+WD_LST+GAP       ,cap=_('&Tools')                        )] #  0 &t
 +[cust_it(tp='listview',t=GAP+20   ,l=GAP      ,r=GAP+4+WD_LST
                        ,b=GAP+HT_LST                                   ,items=itms     ,val=ext_ind            )] #  1     start sel
            # TOOLS ACTS
 +[cust_it(tp='button'  ,t=ACTS_T[1],l=ACTS_L[1],w=ACTS_W               ,cap=_('&Edit...')          ,props='1'  )] #  2 &e  default
 +[cust_it(tp='button'  ,t=ACTS_T[1],l=ACTS_L[2],w=ACTS_W               ,cap=_('&Add...')                       )] #  3 &a
 +[cust_it(tp='button'  ,t=ACTS_T[2],l=ACTS_L[1],w=ACTS_W               ,cap=_('Clo&ne')                        )] #  4 &n
 +[cust_it(tp='button'  ,t=ACTS_T[2],l=ACTS_L[2],w=ACTS_W               ,cap=_('&Delete...')                    )] #  5 &d
 +[cust_it(tp='button'  ,t=ACTS_T[1],l=ACTS_L[4],w=ACTS_W               ,cap=_('&Up')       ,hint=DTLS_MVUP_H   )] #  6 &u
 +[cust_it(tp='button'  ,t=ACTS_T[2],l=ACTS_L[4],w=ACTS_W               ,cap=_('Do&wn')     ,hint=DTLS_MVDN_H   )] #  7 &w
 +[cust_it(tp='button'  ,t=ACTS_T[1],l=ACTS_L[6],r=ACTS_L[7]+ACTS_W     ,cap=_('Set &main for lexers...')
                                                                                            ,hint=DTLS_MNLX_H   )] #  8 &m
            # DLG ACTS
 +[cust_it(tp='button'  ,t=ACTS_T[1],l=DLG_W-GAP2-ACTS_W,w=ACTS_W       ,cap=_('Ad&just...'),hint=DTLS_CUST_H   )] #  9 &j
 +[cust_it(tp='button'  ,t=ACTS_T[2],l=DLG_W-GAP2-ACTS_W,w=ACTS_W       ,cap=_('Close')                         )] # 10
            ), 1)    # start focus
            if ans is None:  break #while
            (ans_i
            ,vals)      = ans
            vals        = vals.splitlines()
            new_ext_ind = int(vals[ 1]) if vals[ 1] else -1
            pass;              #LOG and log('ans_i, vals={}',(ans_i, list(enumerate(vals))))
            pass;              #LOG and log('new_ext_ind={}',(new_ext_ind))
            ans_s       = apx.icase(False,''
                           ,ans_i==  2,'edit'
                           ,ans_i==  3,'add'
                           ,ans_i==  4,'clone'
                           ,ans_i==  5,'del'
                           ,ans_i==  6,'up'
                           ,ans_i==  7,'down'
                           ,ans_i==  8,'main'
                           ,ans_i==  9,'custom'
                           ,ans_i== 10,'close'
                           ,'?')
            if ans_s=='close':
                break #while
            if ans_s=='custom': #Custom
#               custs   = app.dlg_input_ex(10, 'Custom dialog Tools. Align cols with "R"/"C" starts Widths. Start with "-" to hide column.'
                custs   = app.dlg_input_ex(10, _('Custom dialog Tools. Start Widths with "R"/"C" to align. Start with "-" to hide column.')
#               custs   = app.dlg_input_ex(10, 'Custom dialog Tools. Use L,R,C before width to align (empty=L). Use "-" to hide column.'
                    , _('Width of Name    (min 100)')  , prs.get('nm'  , '150')
                    , _('Width of Keys    (min  50)')  , prs.get('keys', '100')
                    , _('Width of File    (min 150)')  , prs.get('file', '180')
                    , _('Width of Params  (min 150)')  , prs.get('prms', '100')
                    , _('Width of Folder  (min 100)')  , prs.get('ddir', '100')
                    , _('Width of Lexers  (min  50)')  , prs.get('lxrs', 'C50')
                    , _('Width of Capture (min  50)')  , prs.get('rslt', 'C50')
                    , _('Width of Saving  (min  30)')  , prs.get('savs', 'C30')
                    , _('List height  (min 200)')      , str(self.dlg_prs.get('h_list', 300))
                    , _('Button width (min 70)')       , str(self.dlg_prs.get('w_btn', 90))
                    )
                if custs is not None:
                    def adapt2min(vmin, cval, can_hide=True):
                        cval    = cval.upper()
                        if can_hide and cval[0]=='-':   return cval
                        cval    = cval.lstrip('-')
                        c1st    = cval[0] if cval[0] in 'LRC' else ''
                        cval    = cval.lstrip('LRC')
                        return    c1st + str(max(vmin, int(cval)))
                    self.dlg_prs['nm']      = adapt2min(100, custs[0], False)
                    self.dlg_prs['keys']    = adapt2min( 50, custs[1], True)
                    self.dlg_prs['file']    = adapt2min(150, custs[2], True)
                    self.dlg_prs['prms']    = adapt2min(150, custs[3], True)
                    self.dlg_prs['ddir']    = adapt2min(100, custs[4], True)
                    self.dlg_prs['lxrs']    = adapt2min( 50, custs[5], True)
                    self.dlg_prs['rslt']    = adapt2min( 50, custs[6], True)
                    self.dlg_prs['savs']    = adapt2min( 30, custs[7], True)
                    self.dlg_prs['h_list']  =       max(200, int(custs[8]))
                    self.dlg_prs['w_btn']   =       max( 70, int(custs[9]))
                    open(EXTS_JSON, 'w').write(json.dumps(self.saving, indent=4))
                continue #while

            if ans_s=='main': #Main lexer tool
                self._dlg_main_tool(0 if new_ext_ind==-1 else ids[new_ext_ind])
                ext_ind     = new_ext_ind
                continue #while
            
            if ans_s=='add': #New
                pttn4run    = {ps['run']:ps['re']           for ps in self.preset}
                test4run    = {ps['run']:ps.get('test', '') for ps in self.preset}
                file4run    = app.dlg_file(True, '!', '', '')   # '!' to disable check "filename exists"
                file4run    = file4run if file4run is not None else ''
                id4ext      = gen_ext_id(self.ext4id)
                run_nm      = os.path.basename(file4run)
                ext         = self._fill_ext({'id':id4ext
                                    ,'nm':(run_nm if file4run else 'tool{}'.format(len(self.exts)))
                                    ,'file':file4run
                                    ,'ddir':os.path.dirname(file4run)
                                    })
                if run_nm in pttn4run:
                    ext['pttn']     = pttn4run.get(run_nm, '')
                    ext['pttn-test']= test4run.get(run_nm, '')
                ed_ans      = self._dlg_config_prop(ext, keys)
                pass;          #LOG and log('fin edit={}',ed_ans)
                if ed_ans is None:
                    continue #while
#               self._gen_ext_crc(ext)
                self.exts  += [ext]
                ids         = [ext['id'] for ext in self.exts]
                ext_ind     = len(self.exts)-1
                new_ext_ind = ext_ind           ## need?

            if new_ext_ind==-1:
                continue #while
                
            what    = ''
            ext_ind = new_ext_ind
            pass;              #LOG and log('ext_ind, ids={}',(ext_ind, ids))
            pass;              #LOG and log('len(self.exts), len(ids)={}',(len(self.exts), len(ids)))
            self.last_ext_id    = ids[ext_ind]
            if False:pass
            
            elif ans_s=='edit':
                pass;          #LOG and log('?? edit self.exts[new_ext_ind]={}',self.exts[new_ext_ind])
                ed_ans  = self._dlg_config_prop(self.exts[new_ext_ind], keys)
                if ed_ans is None or not ed_ans:
                    pass;      #LOG and log('// edit self.exts[new_ext_ind]={}',self.exts[new_ext_ind])
                    continue # while
                pass;          #LOG and log('ok edit self.exts[new_ext_ind]={}',self.exts[new_ext_ind])
                
            elif ans_s=='up' and new_ext_ind>0: #Up
                pass;          #LOG and log('up',())
                (self.exts[new_ext_ind-1]
                ,self.exts[new_ext_ind  ])  = (self.exts[new_ext_ind  ]
                                              ,self.exts[new_ext_ind-1])
                ext_ind = new_ext_ind-1
            elif ans_s=='down' and new_ext_ind<(len(self.exts)-1): #Down
                pass;          #LOG and log('dn',())
                (self.exts[new_ext_ind  ]
                ,self.exts[new_ext_ind+1])  = (self.exts[new_ext_ind+1]
                                              ,self.exts[new_ext_ind  ])
                ext_ind = new_ext_ind+1
            
            elif ans_s=='clone': #Clone
                cln_ext     = copy.deepcopy(self.exts[new_ext_ind])
                cln_ext['id']= gen_ext_id(self.ext4id)
                cln_ext['nm']= cln_ext['nm']+' clone'
#               self._gen_ext_crc(cln_ext)
                self.exts   += [cln_ext]
                ext_ind     = len(self.exts)-1

            elif ans_s=='del': #Del
#               if app.msg_box( 'Delete Tool\n    {}'.format(exkys[new_ext_ind])
                flds    = list(ext_nz_d.keys())
                ext_vls = ext_vlss[new_ext_ind]
                if app.msg_box( _('Delete Tool?\n\n') + '\n'.join(['{}: {}'.format(flds[ind], ext_vls[ind]) 
                                                            for ind in range(len(flds))
                                                       ])
                              , app.MB_YESNO)!=app.ID_YES:
                    continue # while
                id4del  = self.exts[new_ext_ind]['id']
                for lxr in [lxr for lxr,ext_id in self.ext4lxr.items() if ext_id==id4del]:
                    del self.ext4lxr[lxr]
                del self.exts[new_ext_ind]
                ext_ind = min(new_ext_ind, len(self.exts)-1)
                what    = 'delete:'+str(id4del)

            pass;              #LOG and log('?? list _do_acts',)
            self._do_acts(what)
           #while True
       #def dlg_config_list
        
    def _dlg_main_tool(self, ext_id=0):
        lxrs_l  = _get_lexers()
        nm4ids  = {ext['id']:ext['nm'] for ext in self.exts}
        nms     = [ext['nm'] for ext in self.exts]
        ids     = [ext['id'] for ext in self.exts]
        lxr_ind     = 0
        tool_ind    = ids.index(ext_id) if ext_id in ids else 0
        focused     = 1
        while True:
            DLG_W, DLG_H= GAP*3+300+400, GAP*4+300+23*2 -GAP

            lxrs_enm    = ['{}{}'.format(lxr, '  >>>  {}'.format(nm4ids[self.ext4lxr[lxr]]) if lxr in self.ext4lxr else '')
                            for lxr in lxrs_l]

            ans = app.dlg_custom(_('Main Tool for lexers')   ,DLG_W, DLG_H, '\n'.join([]
            # TOOL PROPS
 +[cust_it(tp='label'   ,t=GAP+ 3           ,l=GAP          ,w=400          ,cap=_('&Lexer  >>>  main Tool')    )] #  0 &l
 +[cust_it(tp='listbox' ,t=GAP+23           ,l=GAP          ,r=GAP+400
                        ,b=GAP+23+300                                       ,items=lxrs_enm     ,val=lxr_ind    )] #  1     start sel
 +[cust_it(tp='label'   ,t=GAP+ 3           ,l=GAP+400+GAP  ,w=300          ,cap=_('&Tools')                    )] #  2 &t
 +[cust_it(tp='listbox' ,t=GAP+23           ,l=GAP+400+GAP  ,r=GAP+400+GAP+300
                        ,b=GAP+23+300                                       ,items=nms          ,val=tool_ind   )] #  3     start sel

 +[cust_it(tp='button'  ,t=GAP+23+300+GAP   ,l=GAP          ,w=97           ,cap=_('&Assign tool')              )] #  4 &a
 +[cust_it(tp='button'  ,t=GAP+23+300+GAP   ,l=GAP+97+GAP   ,w=97           ,cap=_('&Break join')               )] #  5 &b
 
 +[cust_it(tp='button'  ,t=GAP+23+300+GAP   ,l=DLG_W-GAP-80 ,w=80           ,cap=_('Close')                     )] #  6
            ), focused)    # start focus
            if ans is None:  
                return None
            (ans_i
            ,vals)      = ans
            vals        = vals.splitlines()
            pass;              #LOG and log('ans_i, vals={}',(ans_i, list(enumerate(vals))))
            ans_s       = apx.icase(False,''
                           ,ans_i== 4,'assign'
                           ,ans_i== 5,'break'
                           ,ans_i== 6,'close'
                           )
            lxr_ind     = int(vals[ 1])
            tool_ind    = int(vals[ 3])
            if ans_s=='close':  return
            changed     = False
            if False:pass
            elif (ans_s=='assign' 
            and   lxr_ind in range(len(lxrs_l)) 
            and   tool_ind in range(len(ids))):      #Assign
                lxr     = lxrs_l[lxr_ind]
                self.ext4lxr[lxr]   = ids[tool_ind]
                ext     = self.ext4id[str(ids[tool_ind])]
                if ','+lxr+',' not in ','+ext['lxrs']+',':
                    ext['lxrs'] = (ext['lxrs']+','+lxr).lstrip(',')
                changed = True

            elif (ans_s=='break' 
            and   lxr_ind in range(len(lxrs_l))
            and   lxrs_l[lxr_ind] in self.ext4lxr):  #Break
                del self.ext4lxr[lxrs_l[lxr_ind]]
                changed = True

            if changed:
                open(EXTS_JSON, 'w').write(json.dumps(self.saving, indent=4))
           #while True
       #def dlg_main_tool
        
    def _dlg_config_prop(self, src_ext, keys=None):
        keys_json   = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'keys.json'
        if keys is None:
            keys    = apx._json_loads(open(keys_json).read()) if os.path.exists(keys_json) else {}
        src_kys     = get_keys_desc('cuda_exttools,run', src_ext['id'], keys)

        ed_ext      = copy.deepcopy(src_ext)
        
        GAP2            = GAP*2    
        PRP1_W, PRP1_L  = (100, GAP)
        PRP2_W, PRP2_L  = (400, PRP1_L+    PRP1_W)
        PRP3_W, PRP3_L  = (100, PRP2_L+GAP+PRP2_W)
        PROP_T          = [GAP*ind+25*(ind-1) for ind in range(20)]   # max 20 rows
        DLG_W, DLG_H    = PRP3_L+PRP3_W+GAP, PROP_T[17]#+GAP
        
        focused         = 1
        while True:
            ed_kys  = get_keys_desc('cuda_exttools,run', ed_ext['id'], keys)
            val_savs= self.savs_vals.index(ed_ext['savs']) if ed_ext is not None else 0
            val_rslt= self.rslt_vals.index(ed_ext['rslt']) if ed_ext is not None else 0
            
            main_for= ','.join([lxr for (lxr,eid) in self.ext4lxr.items() if eid==ed_ext['id']])
            more_s  = json.dumps(_adv_prop('get-dict', ed_ext)).strip('{}').strip()
            ans = app.dlg_custom(_('Tool properties')   ,DLG_W, DLG_H, '\n'.join([]
            # TOOL PROPS
 +[cust_it(tp='label'   ,t=PROP_T[1]+at4lbl ,l=PRP1_L   ,w=PRP1_W   ,cap=_('&Name')                     )] #  0 &n
 +[cust_it(tp='edit'    ,t=PROP_T[1]        ,l=PRP2_L   ,w=PRP2_W   ,val=ed_ext['nm']                   )] #  1
                      
 +[cust_it(tp='label'   ,t=PROP_T[2]+at4lbl ,l=PRP1_L   ,w=PRP1_W   ,cap=_('&File name')                )] #  2 &f
 +[cust_it(tp='edit'    ,t=PROP_T[2]        ,l=PRP2_L   ,w=PRP2_W   ,val=ed_ext['file']                 )] #  3
 +[cust_it(tp='button'  ,t=PROP_T[2]+at4btn ,l=PRP3_L   ,w=PRP3_W   ,cap=_('&Browse...')                )] #  4 &b
 +[cust_it(tp='check'   ,t=PROP_T[3]-2      ,l=PRP2_L   ,w=PRP2_W   ,cap=_('&Shell command')
                                                                    ,val=('1' if ed_ext['shll'] else '0'))]#  5 &s
                      
 +[cust_it(tp='label'   ,t=PROP_T[4]+at4lbl ,l=PRP1_L   ,w=PRP1_W   ,cap=_('&Parameters')               )] #  6 &p
 +[cust_it(tp='edit'    ,t=PROP_T[4]        ,l=PRP2_L   ,w=PRP2_W   ,val=ed_ext['prms']                 )] #  7
 +[cust_it(tp='button'  ,t=PROP_T[4]+at4btn ,l=PRP3_L   ,w=PRP3_W   ,cap=_('A&dd...')                   )] #  8 &a
                      
 +[cust_it(tp='label'   ,t=PROP_T[5]+at4lbl ,l=PRP1_L   ,w=PRP1_W   ,cap=_('&Initial folder')           )] #  9 &i
 +[cust_it(tp='edit'    ,t=PROP_T[5]        ,l=PRP2_L   ,w=PRP2_W   ,val=ed_ext['ddir']                 )] # 10
 +[cust_it(tp='button'  ,t=PROP_T[5]+at4btn ,l=PRP3_L   ,w=PRP3_W   ,cap=_('B&rowse...')                )] # 11 &r
                      
 +[cust_it(tp='label'   ,t=PROP_T[6]+at4lbl ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Lexers')                    )] # 12
 +[cust_it(tp='edit'    ,t=PROP_T[6]        ,l=PRP2_L   ,w=PRP2_W   ,val=ed_ext['lxrs'] ,props='1,0,1'  )] # 13     ro,mono,border
 +[cust_it(tp='button'  ,t=PROP_T[6]+at4btn ,l=PRP3_L   ,w=PRP3_W   ,cap=_('Le&xers...')                )] # 14 &x
                      
 +[cust_it(tp='label'   ,t=PROP_T[7]+at4lbl ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Main for')                  )] # 15
 +[cust_it(tp='edit'    ,t=PROP_T[7]        ,l=PRP2_L   ,w=PRP2_W   ,val=main_for       ,props='1,0,1'  )] # 16     ro,mono,border
 +[cust_it(tp='button'  ,t=PROP_T[7]+at4btn ,l=PRP3_L   ,w=PRP3_W   ,cap=_('Set &main...')              )] # 17 &m
                      
 +[cust_it(tp='label'   ,t=PROP_T[8]+at4lbl ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Sa&ve before')              )] # 18 &v
 +[cust_it(tp='combo_ro',t=PROP_T[8]+at4cbo ,l=PRP2_L   ,w=PRP2_W   ,items=self.savs_caps
                                                                    ,val=val_savs                       )] # 19     start sel
                      
 +[cust_it(tp='label'   ,t=PROP_T[9]+at4lbl ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Hotkey')                    )] # 20
 +[cust_it(tp='edit'    ,t=PROP_T[9]        ,l=PRP2_L   ,w=PRP2_W   ,val=ed_kys         ,props='1,0,1'  )] # 21     ro,mono,border
 +[cust_it(tp='button'  ,t=PROP_T[9]+at4btn ,l=PRP3_L   ,w=PRP3_W   ,cap=_('Assi&gn...')                )] # 22 &g
                      
 +[cust_it(tp='label'   ,t=PROP_T[11]+at4lbl,l=PRP1_L   ,w=PRP1_W   ,cap=_('&Capture output')           )] # 23 &c
 +[cust_it(tp='combo_ro',t=PROP_T[11]+at4cbo,l=PRP2_L   ,w=PRP2_W   ,items=self.rslt_caps
                                                                    ,val=val_rslt                       )] # 24     start sel
                      
 +[cust_it(tp='label'   ,t=PROP_T[12]+at4lbl,l=PRP1_L   ,w=PRP1_W   ,cap=_('Encoding')                  )] # 25
 +[cust_it(tp='edit'    ,t=PROP_T[12]       ,l=PRP2_L   ,w=PRP2_W   ,val=ed_ext['encd'] ,props='1,0,1'  )] # 26     ro,mono,border
 +[cust_it(tp='button'  ,t=PROP_T[12]+at4btn,l=PRP3_L   ,w=PRP3_W   ,cap=_('S&elect...')                )] # 27 &e
                      
 +[cust_it(tp='label'   ,t=PROP_T[13]+at4lbl,l=PRP1_L   ,w=PRP1_W   ,cap=_('Pattern')                   )] # 28
 +[cust_it(tp='edit'    ,t=PROP_T[13]       ,l=PRP2_L   ,w=PRP2_W   ,val=ed_ext['pttn'] ,props='1,0,1'  )] # 29     ro,mono,border
 +[cust_it(tp='button'  ,t=PROP_T[13]+at4btn,l=PRP3_L   ,w=PRP3_W   ,cap=_('Se&t...')                   )] # 30 &e
                      
 +[cust_it(tp='label'   ,t=PROP_T[14]+at4lbl,l=PRP1_L   ,w=PRP1_W   ,cap=_('Advanced')                  )] # 31
 +[cust_it(tp='edit'    ,t=PROP_T[14]       ,l=PRP2_L   ,w=PRP2_W   ,val=more_s         ,props='1,0,1'  )] # 32     ro,mono,border
 +[cust_it(tp='button'  ,t=PROP_T[14]+at4btn,l=PRP3_L   ,w=PRP3_W   ,cap=_('Set...')                    )] # 33
            # DLG ACTS
 +[cust_it(tp='button'  ,t=PROP_T[16]       ,l=GAP      ,w=PRP3_W       ,cap=_('Help')                  )] # 34
 +[cust_it(tp='button'  ,t=PROP_T[16]       ,l=DLG_W-GAP*2-100*2,w=100  ,cap=_('OK')    ,props='1'      )] # 35     default
 +[cust_it(tp='button'  ,t=PROP_T[16]       ,l=DLG_W-GAP*1-100*1,w=100  ,cap=_('Cancel')                )] # 36
            ), focused)    # start focus
            if ans is None:  
                return None
            (ans_i
            ,vals)      = ans
            vals        = vals.splitlines()
            pass;              #LOG and log('ans_i, vals={}',(ans_i, list(enumerate(vals))))
            ans_s       = apx.icase(False,''
                           ,ans_i==  4,'file'
                           ,ans_i==  8,'prms'
                           ,ans_i== 11,'ddir'
                           ,ans_i== 14,'lxrs'
                           ,ans_i== 17,'main'
                           ,ans_i== 22,'hotkeys'
                           ,ans_i== 27,'encd'
                           ,ans_i== 30,'pttn'
                           ,ans_i== 33,'more'
                           ,ans_i== 34,'help'
                           ,ans_i== 35,'save'
                           ,ans_i== 36,'cancel'
                           ,'?')
            ed_ext['nm']    =   vals[  1]
            ed_ext['file']  =   vals[  3]
            ed_ext['shll']  =   vals[  5]=='1'
            ed_ext['prms']  =   vals[  7]
            ed_ext['ddir']  =   vals[ 10]
            ed_ext['lxrs']  =   vals[ 13]
            ed_ext['savs']  = self.savs_vals[int(
                                vals[ 19])]
            ed_ext['rslt']  = self.rslt_vals[int(
                                vals[ 24])]
            ed_ext['encd']  =   vals[ 26]
#           ed_ext['pttn']  =   vals[ 29]
                
            if ans_s=='cancel':
                return None
            if ans_s=='save':
                #Checks
                if False:pass
                elif not ed_ext['nm']:
                    app.msg_box(_('Set name'), app.MB_OK)
                    focused = 1
                    continue #while
                elif not ed_ext['file']:
                    app.msg_box(_('Set file'), app.MB_OK)
                    focused = 3
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
#               self._gen_ext_crc(src_ext)
                return True

            if False:pass
            elif ans_s=='help':
                app.dlg_custom(EXT_HELP_CAP, GAP*2+550, GAP*3+25+450, '\n'.join([]
 +[cust_it(tp='memo'    ,t=GAP          ,l=GAP          ,r=GAP+550  ,props='1,1,1'
                        ,b=GAP+450                                  ,val=EXT_HELP_BODY  )] #  0    ro,mono,border
 +[cust_it(tp='button'  ,t=GAP+450+GAP  ,l=GAP+550-90   ,w=90       ,cap='&Close'       )] #  1
                ), 1)    # start focus
                continue #while

            if ans_s=='main': #Lexer main tool
                self._dlg_main_tool(ed_ext['id'])
                continue #while
            
            elif ans_s=='file': #File
                file4run= app.dlg_file(True, '!'+ed_ext['file'], '', '')# '!' to disable check "filename exists"
                if file4run is not None:
                    ed_ext['file'] = file4run
            
            elif ans_s=='ddir': #File
                file4dir= app.dlg_file(True, '!', ed_ext['ddir'], '')   # '!' to disable check "filename exists"
                if file4dir is not None:
                    ed_ext['ddir'] = os.path.dirname(file4dir)

            elif ans_s=='prms': #Append param {*}
                prms_l  =([]
                        +[_('{AppDir}\tDirectory with app executable')]
                        +[_('{AppDrive}\t(Win only) Disk of app executable, eg "C:"')]
                        +[_('{FileName}\tFull path')]
                        +[_('{FileDir}\tFolder path, without file name')]
                        +[_('{FileNameOnly}\tFile name only, without folder path')]
                        +[_('{FileNameNoExt}\tFile name without extension and path')]
                        +[_('{FileExt}\tExtension')]
                        +[_('{CurrentLine}\tText of current line')]
                        +[_('{CurrentLineNum}\tNumber of current line')]
                        +[_('{CurrentLineNum0}\tNumber of current line (0-based)')]
                        +[_('{CurrentColumnNum}\tNumber of current column')]
                        +[_('{CurrentColumnNum0}\tNumber of current column (0-based)')]
                        +[_('{SelectedText}\tText')]
                        +[_('{Interactive}\tText will be asked at each running')]
                        +[_('{InteractiveFile}\tFile name will be asked')])
                prm_i   = app.dlg_menu(app.MENU_LIST_ALT, '\n'.join(prms_l))
                if prm_i is not None:
                    ed_ext['prms']  = (ed_ext['prms'] + (' '+prms_l[prm_i].split('\t')[0])).lstrip()

            elif ans_s=='hotkeys': #Hotkeys
                app.dlg_hotkeys('cuda_exttools,run,'+str(ed_ext['id']))
                keys    = apx._json_loads(open(keys_json).read()) if os.path.exists(keys_json) else {}
            
            elif ans_s=='lxrs': #Lexers only
                lxrs    = ','+ed_ext['lxrs']+','
                lxrs_l  = _get_lexers()
                sels    = ['1' if ','+lxr+',' in lxrs else '0' for lxr in lxrs_l]
                crt     = str(sels.index('1') if '1' in sels else 0)
                ans     = app.dlg_custom(_('Select lexers')   ,GAP+200+GAP, GAP+400+GAP+24+GAP, '\n'.join([]
 +[cust_it(tp='checklistbox',t=GAP          ,l=GAP          ,r=GAP+200
                            ,b=GAP+400                                  ,items=lxrs_l   
                                                                        ,val=crt+';'+','.join(sels) )] #  0     start sel
 +[cust_it(tp='button'      ,t=GAP+400+GAP  ,l=    200-140  ,w=70       ,cap=_('OK'),props='1'      )] #  1     default
 +[cust_it(tp='button'      ,t=GAP+400+GAP  ,l=GAP+200- 70  ,w=70       ,cap=_('Cancel')            )] #  2
                ), 0)    # start focus
                if ans is not None and ans[0]==1:
                    crt,sels= ans[1].splitlines()[0].split(';')
                    sels    = sels.strip(',').split(',')
                    lxrs    = [lxr for (ind,lxr) in enumerate(lxrs_l) if sels[ind]=='1']
                    ed_ext['lxrs'] = ','.join(lxrs)
            
            elif ans_s=='encd': #Enconing
                enc_nms = get_encoding_names()
                enc_ind = app.dlg_menu(app.MENU_LIST_ALT, '\n'.join(enc_nms))
                if enc_ind is not None:
                    ed_ext['encd'] = enc_nms[enc_ind].split('\t')[0]

            elif ans_s=='pttn': #Pattern
                pass;          #LOG and log('?? ed_ext[pttn-data]={}',ed_ext['pttn-data'])
                (new_pttn,new_test)     = self._dlg_pattern(ed_ext['pttn'], ed_ext.get('pttn-test', ''), os.path.basename(ed_ext['file']))
                if new_pttn is not None:
                    ed_ext['pttn']      = new_pttn
                    ed_ext['pttn-test'] = new_test
                pass;          #LOG and log('ok ed_ext[pttn-data]={}',ed_ext['pttn-data'])
            
            elif ans_s=='more': #Advanced
                lbeds   = [] 
                for (i, a) in enumerate(ADV_PROPS):
                    lbeds += ([] 
 +[cust_it(tp='label'   ,t=GAP+i*50     ,l=GAP  ,w=500  ,cap=F('("{}") {}', a['key'], a['cap']),hint=a['hnt']   )]  # i*2
 +[cust_it(tp='edit'    ,t=GAP+i*50+18  ,l=GAP  ,w=500  ,val=ed_ext.get(    a['key'], a['def'])                 )]) # i*2+1
                   #for (i, a)
                avd_h   = len(ADV_PROPS)*50
                ans     = app.dlg_custom(_('Advanced properties'), GAP+500+GAP, GAP+avd_h+GAP+24+GAP, '\n'.join([]
 +lbeds
 +[cust_it(tp='button'  ,t=GAP+avd_h+GAP,l=    500-140  ,w=70   ,cap=_('OK'),props='1'                          )]  # 2*len()    default
 +[cust_it(tp='button'  ,t=GAP+avd_h+GAP,l=GAP+500- 70  ,w=70   ,cap=_('Cancel')                                )]  # 2*len()+1
                    ), 0)    # start focus
                if ans is None or ans[0]==2*len(ADV_PROPS)+1:continue#while
                adv_vals= ans[1].splitlines()
                for (i, a) in enumerate(ADV_PROPS):
                    ictrl   = i*2+1
                    if adv_vals[ictrl]==a['def']:
                        ed_ext.pop(     a['key'], None)
                    else:
                        ed_ext[         a['key']]= adv_vals[ictrl]
                   #for (i, a)
           #while True
       #def _dlg_config_prop

    def _dlg_pattern(self, pttn_re, pttn_test, run_nm):
        pass;                  #LOG and log('pttn_re, pttn_test={}',(pttn_re, pttn_test))
        grp_dic     = {}
        if pttn_re and pttn_test:
            grp_dic = re.search(pttn_re, pttn_test).groupdict('') if re.search(pttn_re, pttn_test) is not None else {}
        
        while True:
            focused     = 1
            DLG_W, DLG_H= GAP+550+GAP, GAP+250#+GAP
            ans = app.dlg_custom(_('Tool "{}" output pattern').format(run_nm)   ,DLG_W, DLG_H, '\n'.join([]
            # RE
 +[cust_it(tp='label'   ,t=GAP          ,l=GAP              ,w=300              ,cap=_('&Regular expression'))]#  0 &r
 +[cust_it(tp='edit'    ,t=GAP+18       ,l=GAP              ,r=DLG_W-GAP*2-70   ,val=pttn_re                )] #  1
 +[cust_it(tp='button'  ,t=GAP+18+at4btn,l=DLG_W-GAP*1-70   ,w=70               ,cap='&?..'                 )] #  2 &?
            # Testing
 +[cust_it(tp='label'   ,t= 60          ,l=GAP              ,w=300              ,cap=_('Test &output line') )] #  3 &o
 +[cust_it(tp='edit'    ,t= 60+18       ,l=GAP              ,r=DLG_W-GAP*2-70   ,val=pttn_test              )] #  4
 +[cust_it(tp='button'  ,t= 60+18+at4btn,l=DLG_W-GAP*1-70   ,w=70               ,cap=_('&Test')             )] #  5 &t

 +[cust_it(tp='label'   ,t=110+GAP*0+23*0       ,l=GAP+ 80  ,w=300              ,cap=_('Testing results')   )] #  6
 +[cust_it(tp='label'   ,t=110+GAP*0+23*1+at4lbl,l=GAP      ,w=80               ,cap=_('Filename')          )] #  7
 +[cust_it(tp='edit'    ,t=110+GAP*0+23*1       ,l=GAP+ 80  ,r=DLG_W-GAP*2-70   ,props='1,0,1'
                                                                                ,val=grp_dic.get('file', ''))] #  8
 +[cust_it(tp='label'   ,t=110+GAP*1+23*2+at4lbl,l=GAP      ,w=80               ,cap=_('Line')              )] #  9
 +[cust_it(tp='edit'    ,t=110+GAP*1+23*2       ,l=GAP+ 80  ,r=DLG_W-GAP*2-70   ,props='1,0,1'
                                                                                ,val=grp_dic.get('line', ''))] # 10
 +[cust_it(tp='label'   ,t=110+GAP*2+23*3+at4lbl,l=GAP      ,w=80               ,cap=_('Column')            )] # 11
 +[cust_it(tp='edit'    ,t=110+GAP*2+23*3       ,l=GAP+ 80  ,r=DLG_W-GAP*2-70   ,props='1,0,1'
                                                                                ,val=grp_dic.get('col', '') )] # 12
            # Preset
 +[cust_it(tp='button'  ,t=DLG_H-GAP-24 ,l=GAP              ,w=130              ,cap=_('Load &preset...')   )] # 13 &p
 +[cust_it(tp='button'  ,t=DLG_H-GAP-24 ,l=GAP+130+GAP      ,w=130              ,cap=_('&Save as preset...'))] # 14 &s
            # OK
 +[cust_it(tp='button'  ,t=DLG_H-GAP-24 ,l=    550-140      ,w=70               ,cap=_('OK'),props='1'      )] # 15     default
 +[cust_it(tp='button'  ,t=DLG_H-GAP-24 ,l=GAP+550- 70      ,w=70               ,cap=_('Cancel')            )] # 16
            ), focused)    # start focus
            if ans is None:  
                return (None, None)
            (ans_i
            ,vals)      = ans
            vals        = vals.splitlines()
            ans_s       = apx.icase(False,''
                           ,ans_i== 2,'help'
                           ,ans_i== 5,'test'
                           ,ans_i==13,'load'
                           ,ans_i==14,'save'
                           ,ans_i==15,'ok'
                           ,ans_i==16,'cancel'
                           )
            pass;              #LOG and log('ans_s, ans_i, vals={}',(ans_s, ans_i, list(enumerate(vals))))
            pttn_re     =     vals[ 1]
            pttn_test   =     vals[ 4]
            
            if ans_s == 'cancel':
                return (None, None)
            if False:pass
            elif ans_s == 'ok':
                return (pttn_re, pttn_test)
            
            elif ans_s == 'help':
                app.msg_box(''
                           +'These groups will be used for navigation:'
                           +'\n   (?P<file>_) for filename (default - current file name),'
                           +'\n   (?P<line>_) for number of line (default - 1),'
                           +'\n   (?P<col>_) for number of column (default - 1).'
                           +'\n   (?P<line0>_) for number of line (0-based, default - 0),'
                           +'\n   (?P<col0>_) for number of column (0-based, default - 0).'
                           +'\n'
                           +'\nFull syntax documentation: https://docs.python.org/3/library/re.html'
                , app.MB_OK)
            
            elif ans_s == 'test':
                grp_dic = re.search(pttn_re, pttn_test).groupdict('') if re.search(pttn_re, pttn_test) is not None else {}
            
            elif ans_s == 'load':
                ps_nms  = ['{}\t{}'.format(ps['name'], ps['run']) for ps in self.preset]
                ps_ind  = app.dlg_menu(app.MENU_LIST, '\n'.join(ps_nms))
                if ps_ind is not None:
                    pttn_re     = self.preset[ps_ind]['re']
                    pttn_test   = self.preset[ps_ind].get('test', '')
                    grp_dic     = re.search(pttn_re, pttn_test).groupdict('') if re.search(pttn_re, pttn_test) is not None else {}
            
            elif ans_s == 'save':
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
       #def dlg_pattern
        
#   def _gen_ext_crc(self, ext):
#       ''' Generate 32-bit int by ext-props '''
#       text    = '|'.join([str(ext[k]) for k in ext])
#       data    = text.encode()
#       crc     = zlib.crc32(data) & 0x0fffffff
#       self.id2crc[ext['id']] = crc

    def _fill_ext(self, ext):
        ext.pop('capt', None)
        ext.pop('name', None)
        if not ext['nm']:
            ext['nm']='tool'+str(random.randint(100, 999))
        ext['ddir'] = ext.get('ddir', '')
        ext['shll'] = ext.get('shll', 'N')=='Y' if str(ext.get('shll', 'N'))    in 'NY'            else ext.get('shll', False)
        ext['prms'] = ext.get('prms', '')
        ext['savs'] = ext.get('savs', SAVS_N)
        ext['rslt'] = ext.get('rslt', RSLT_N)   if     ext.get('rslt', RSLT_N)  in self.rslt_vals  else RSLT_N
        ext['encd'] = ext.get('encd', '')
        ext['lxrs'] = ext.get('lxrs', '')
        ext['pttn'] = ext.get('pttn', '')
#       self._gen_ext_crc(ext)
        return ext

   #class Command

def _adv_prop(act, ext, par=''):
    core_props  = ('id','nm','file','ddir','shll','prms','savs','rslt','encd','lxrs','pttn','pttn-test')
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

def subst_props(prm, file_nm, cCrt=-1, rCrt=-1, ext_nm=''):
    if '{' not in prm:  return prm
    app_dir = app.app_path(app.APP_DIR_EXE)
    if      '{AppDir}'            in prm: prm = prm.replace('{AppDir}'       ,   app_dir)
    if      '{AppDrive}'          in prm: prm = prm.replace('{AppDrive}'     ,   app_dir[0:2] if os.name=='nt' and app_dir[1]==':' else '')
            
    if      '{FileName}'          in prm: prm = prm.replace('{FileName}'     ,                          file_nm)
    if      '{FileDir}'           in prm: prm = prm.replace('{FileDir}'      ,          os.path.dirname(file_nm))
    if      '{FileNameOnly}'      in prm: prm = prm.replace('{FileNameOnly}' ,         os.path.basename(file_nm))
    if      '{FileNameNoExt}'     in prm: prm = prm.replace('{FileNameNoExt}','.'.join(os.path.basename(file_nm).split('.')[0:-1]))
    if      '{FileExt}'           in prm: prm = prm.replace('{FileExt}'      ,         os.path.basename(file_nm).split('.')[-1])

    if rCrt!=-1:
        if  '{CurrentLine}'       in prm: prm = prm.replace('{CurrentLine}'     , ed.get_text_line(rCrt))
        if  '{CurrentLineNum}'    in prm: prm = prm.replace('{CurrentLineNum}'  , str(1+rCrt))
        if  '{CurrentLineNum0}'   in prm: prm = prm.replace('{CurrentLineNum0}' , str(  rCrt))
        if  '{CurrentColumnNum}'  in prm: prm = prm.replace('{CurrentColumnNum}', str(1+ed.convert(app.CONVERT_CHAR_TO_COL, cCrt, rCrt)[0]))
        if  '{CurrentColumnNum0}' in prm: prm = prm.replace('{CurrentColumnNum0}',str(  ed.convert(app.CONVERT_CHAR_TO_COL, cCrt, rCrt)[0]))
        if  '{SelectedText}'      in prm: prm = prm.replace('{SelectedText}'    , ed.get_text_sel())

    if '{Interactive}' in prm:
        ans = app.dlg_input('Param for call {}'.format(ext_nm), '')
        if ans is None: return
        prm = prm.replace('{Interactive}'     , ans)
    if '{InteractiveFile}' in prm:
        ans = app.dlg_file(True, '!', '', '')   # '!' to disable check "filename exists"
        if ans is None: return
        prm = prm.replace('{InteractiveFile}' , ans)
    return prm

def gen_ext_id(ids):
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

def _get_lexers():
    lxrs_l  = app.lexer_proc(app.LEXER_GET_LIST, '').splitlines()
    lxrs_l  = [lxr for lxr in lxrs_l if app.lexer_proc(app.LEXER_GET_ENABLED, lxr)]
    lxrs_l += ['(none)']
    return lxrs_l
   #def _get_lexers

def _test_json(js):
    try:
        json.loads(js)
    except ValueError as exc:
        app.msg_box(str(exc), app.MB_OK)
        return False
    return True
   #def _test_json

def fit_str_json(cfg_raw):
    """ Adapt str-json to correct form (for eval)
            Delete comments
            { smth:     ==>     { "smth":
            , smth:     ==>     , "smth":
            { ,         ==>     {
            [ ,         ==>     [
    """
    cfg_fit     = cfg_raw
    cfg_fit     = re.sub(r'#.*'             , ''         , cfg_fit)         # del comments
    cfg_fit     = re.sub(r'{(\s*) ?(\w+):'  , r'{\1"\2":', cfg_fit)         # {   ver:2     ==>     {   "ver":2
    cfg_fit     = re.sub(       r'{(\w+):'  ,   r'{"\1":', cfg_fit)         #    {ver:2     ==>        {"ver":2
    cfg_fit     = re.sub(r',(\s*) ?(\w+):'  , r',\1"\2":', cfg_fit)         # ,   ver:2     ==>     ,   "ver":2
    cfg_fit     = re.sub(       r',(\w+):'  ,   r',"\1":', cfg_fit)         #    ,ver:2     ==>        ,"ver":2
    cfg_fit     = re.sub( r'{(\s*),'        , r'{\1 '    , cfg_fit, re.S)   # { ,     ==>           {
#   cfg_fit     = re.sub( r',(\s*)}'        , r' \1}'    , cfg_fit, re.S)   # , }     ==>             }
    cfg_fit     = re.sub(r'\[(\s*),'        , r'[\1 '    , cfg_fit, re.S)   # [ ,     ==>           [
#   cfg_fit     = re.sub( r',(\s*)\]'       , r' \1]'    , cfg_fit, re.S)   # , ]     ==>             ]
    pass;                      #log('cfg_fit={}',cfg_fit)
    return cfg_fit
   #def fit_str_json

if __name__ == '__main__' :     # Tests
    Command().dlg_config()    #??
        
'''
ToDo
[-][kv-kv][09dec15] Run test cmd
[+][kv-kv][11jan16] Parse output with re
[?][kv-kv][11jan16] Use PROC_SET_ESCAPE
[ ][kv-kv][19jan16] Use control top with sys.platform
[ ][kv-kv][19jan16] Opt for auto-to-first_rslt
'''
