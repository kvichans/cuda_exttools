''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '1.2.3 2016-05-06'
ToDo: (see end of file)
'''

import  os, json, random, subprocess, shlex, copy, collections, re, zlib
import  cudatext            as app
from    cudatext        import ed
import  cudatext_cmd        as cmds
import  cudax_lib           as apx
from    cudax_lib       import log
from    .encodings      import *
from    .cd_plug_lib    import *

# I18N
_       = get_translation(__file__)

pass;                           # Logging
pass;                           from pprint import pformat
pass;                           LOG = (-2==-2)  # Do or dont logging.
c10,c13,l= chr(10),chr(13),chr(13)

JSON_FORMAT_VER = '20151209'
EXTS_JSON       = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'exttools.json'
#PRESET_JSON     = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'exttools-preset.json'

ADV_PROPS       = [ {'key':'source_tab_as_blanks'
                    ,'cap':_('Consider TAB as "N spaces" to interpret output column')
                   #,'cap':'Output column numbers are counted with replace TAB with N spaces'
                    ,'hnt':_('Set 8 for a Tool likes "tidy"')
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
GAP     = 5

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
        self.rslt_v2c   = {RSLT_N:  RSLT_NO
                          ,RSLT_OP: RSLT_TO_PANEL
                          ,RSLT_OPA:RSLT_TO_PANEL_AP
                          ,RSLT_ND: RSLT_TO_NEWDOC
                          ,RSLT_CB: RSLT_TO_CLIP
                          ,RSLT_SEL:RSLT_REPL_SEL}

        # Saving data
        self.saving     = apx._json_loads(open(EXTS_JSON).read()) if os.path.exists(EXTS_JSON) else {
                             'ver':JSON_FORMAT_VER
                            ,'list':[]
                            ,'dlg_prs':{}
                            ,'ext4lxr':{}
                            ,'preset':[]
                            ,'umacrs':[]
                            }
        if self.saving.setdefault('ver', '') < JSON_FORMAT_VER:
            # Adapt to new format
            pass
        self.dlg_prs    = self.saving.setdefault('dlg_prs', {})
        self.ext4lxr    = self.saving.setdefault('ext4lxr', {})
        self.preset     = self.saving.setdefault('preset', [])
        self.umacrs     = self.saving.setdefault('umacrs', [])
        self.exts       = self.saving['list']
            
        # Runtime data
        self.ext4id     = {str(ext['id']):ext for ext in self.exts}
        self.crcs       = {}
        self.last_crc   = -1
        self.last_ext_id= 0
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
        
    def adapt_menu(self, id_menu=0):
        ''' Add or change top-level menu ExtTools
            Param id_menu points to exist menu item (ie by ConfigMenu) for filling
        '''
        pass;                  #LOG and log('id_menu={}',id_menu)
        PLUG_HINT   = '_'+'cuda_exttools:adapt_menu'      # "_" is sign for ConfigMenu. ":" is subst for "," to avoid call "import ..."
        if id_menu!=0:
            # Use this id
            app.app_proc(app.PROC_MENU_CLEAR, str(id_menu))
        else:
            top_nms = app.app_proc(app.PROC_MENU_ENUM, 'top')
            if PLUG_HINT in top_nms:
                # Reuse id from 'top'
                inf     = [inf for inf in top_nms.splitlines() if PLUG_HINT in inf][0]     ##?? 
                id_menu = inf.split('|')[2]
                app.app_proc(app.PROC_MENU_CLEAR, id_menu)
            else:
                # Create AFTER Plugins
                top_nms = top_nms.splitlines()
                pass;              #LOG and log('top_nms={}',top_nms)
                if app.app_exe_version() >= '1.0.131':
                    plg_ind = [i for (i,nm) in enumerate(top_nms) if '|plugins' in nm][0]
                else: # old, pre i18n
                    plg_ind = top_nms.index('&Plugins|')                                                    ##?? 
                id_menu = app.app_proc( app.PROC_MENU_ADD, '{};{};{};{}'.format('top', PLUG_HINT, _('&Tools'), 1+plg_ind))
        # Fill
        def hotkeys_desc(cmd_id):
            hk_s= get_hotkeys_desc(cmd_id)
            hk_s= '\t\t'+hk_s if hk_s else hk_s
            return hk_s
        hk_s    = hotkeys_desc(            'cuda_exttools,dlg_config')
        app.app_proc(app.PROC_MENU_ADD, '{};cuda_exttools,dlg_config;{}'.format(    id_menu,    _('Con&fig...')+hk_s))
        hk_s    = hotkeys_desc(            'cuda_exttools,run_lxr_main')
        app.app_proc(app.PROC_MENU_ADD, '{};cuda_exttools,run_lxr_main;{}'.format(  id_menu,    _('R&un lexer main Tool')+hk_s))
        id_rslt = app.app_proc( app.PROC_MENU_ADD, '{};{};{}'.format(               id_menu, 0, _('Resul&ts')))
        hk_s    = hotkeys_desc(            'cuda_exttools,show_next_result')
        app.app_proc(app.PROC_MENU_ADD, '{};cuda_exttools,show_next_result;{}'.format(id_rslt,  _('Nex&t Tool result')+hk_s))
        hk_s    = hotkeys_desc(            'cuda_exttools,show_prev_result')
        app.app_proc(app.PROC_MENU_ADD, '{};cuda_exttools,show_prev_result;{}'.format(id_rslt,  _('&Previous Tool result'+hk_s)))
        if 0==len(self.exts):
            return
        app.app_proc(app.PROC_MENU_ADD, '{};;-'.format(id_menu))
        for ext in self.exts:
            hk_s= hotkeys_desc(              f('cuda_exttools,run,{}',                   ext['id']))
            app.app_proc(app.PROC_MENU_ADD, '{};cuda_exttools,run,{};{}'.format(id_menu, ext['id'], ext['nm']+hk_s))
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
            self.adapt_menu()
       #def _do_acts

    def run_lxr_main(self):
        lxr     = ed.get_prop(app.PROP_LEXER_FILE)
        if lxr not in self.ext4lxr:
            return app.msg_status(_('No main Tool for lexer "{}"').format(lxr))
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
            return app.msg_status(_('No Tool: {}').format(ext_id))
        nm      = ext['nm']
        lxrs    = ext['lxrs']
        lxr_cur = ed.get_prop(app.PROP_LEXER_FILE)
        lxr_cur = lxr_cur if lxr_cur else '(none)' 
        pass;                  #LOG and log('nm="{}", lxr_cur="{}", lxrs="{}"',nm, lxr_cur, lxrs)
        if (lxrs
        and not (','+lxr_cur+',' in ','+lxrs+',')):
            return app.msg_status(_('Tool "{}" is not suitable for lexer "{}". It works only with "{}"').format(nm, lxr_cur, lxrs))

        jext    = ext.get('jext')
        if jext:
            for subid in jext:
                if not self.run(subid):
                    return False
            return True
        
        cmnd    = ext['file']
        prms_s  = ext['prms']
        ddir    = ext['ddir']
        pass;                  #LOG and log('nm="{}", cmnd="{}", ddir="{}", prms_s="{}"',nm, cmnd, ddir, prms_s)
        
        # Saving
        if SAVS_Y==ext.get('savs', SAVS_N):
            if not app.file_save():  return app.msg_status(_('Cancel running Tool "{}"'.format(nm)))
        if SAVS_A==ext.get('savs', SAVS_N):
            ed.cmd(cmds.cmd_FileSaveAll)
        
        # Preparing
        file_nm = ed.get_filename()
        if  not file_nm and (
            '{File' in cmnd
        or  '{File' in prms_s
        or  '{File' in ddir ):  return app.msg_status(_('Cannot run Tool "{}" for untitled tab'.format(nm)))
        (cCrt, rCrt
        ,cEnd, rEnd)    = ed.get_carets()[0]
        umc_vals= self._calc_umc_vals()
        prms_l  = shlex.split(prms_s)
        for ind, prm in enumerate(prms_l):
            prm_raw = prm
            prm     = _subst_props(prm,  file_nm, cCrt, rCrt, ext['nm'], umcs=umc_vals)
            if prm_raw != prm:
                prms_l[ind] = prm
#               prms_l[ind] = shlex.quote(prm)
           #for ind, prm
        cmnd        = _subst_props(cmnd, file_nm, cCrt, rCrt, ext['nm'], umcs=umc_vals)
        ddir        = _subst_props(ddir, file_nm, cCrt, rCrt, ext['nm'], umcs=umc_vals)

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
            else: # rslt==RSLT_OPA
                pass
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
            
        return True
       #def run
       
    def on_output_nav(self, ed_self, output_line, crc_tag):
        pass;                  #LOG and log('output_line, crc_tag={}',(output_line, crc_tag))
        
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
        pass;                  #LOG and log('nav_file, nav_line, nav_col={}',(nav_file, nav_line, nav_col))
        bs_dir  = ext['ddir']
        bs_dir  = os.path.dirname(crc_inf['pth']) \
                    if not bs_dir else  \
                  _subst_props(bs_dir, crc_inf['pth'], umcs=self._calc_umc_vals())
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

        crc_inf     = self.crcs.get(self.last_crc, {})
        ext         = crc_inf.get('ext')
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
            app.msg_status(_('No more results for navigation'))
       #def _show_result
       
    def dlg_config(self):
        if app.app_api_version()<FROM_API_VERSION:  return app.msg_status(_('Need update CudaText'))

        keys_json   = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'keys.json'
        
        ids     = [ext['id'] for ext in self.exts]
        ext_ind = ids.index(self.last_ext_id) if self.last_ext_id in ids else min(0, len(ids)-1)

        DTLS_JOIN_H     = _('Join several Tools to single Tool')
        DTLS_MVUP_H     = _('Move current Tool to upper position')
        DTLS_MVDN_H     = _('Move current Tool to lower position')
        DTLS_MNLX_H     = _('For call by command "Run lexer main Tool"')
        DTLS_USMS_H     = _("Edit list of user's macros to use in Tool properties")
        DTLS_CUST_H     = _('Change this dialog sizes')

        GAP2    = GAP*2    
        prs     = self.dlg_prs
        pass;                  #LOG and log('prs={}',prs)
        while True:
            keys        = apx._json_loads(open(keys_json).read()) if os.path.exists(keys_json) else {}
            ext_nz_d    = collections.OrderedDict([
                           (_('Name')           ,prs.get('nm'  , '150'))
                          ,(_('Keys')           ,prs.get('keys', '100'))
                          ,(_('File | [Tools]') ,prs.get('file', '180'))
                          ,(_('Params')         ,prs.get('prms', '100'))
                          ,(_('Folder')         ,prs.get('ddir', '100'))
                          ,(_('Lexers')         ,prs.get('lxrs', 'C50'))
                          ,(_('Capture')        ,prs.get('rslt', 'C50'))
                          ,(_('Saving')         ,prs.get('savs', 'C30'))
                          ])
            ACTS_W          = prs.get('w_btn', 90)
            AW2             = int(ACTS_W/2)
            WD_LST, HT_LST  = (sum([int(w.lstrip('LRC')) for w in ext_nz_d.values() if w[0]!='-'])+len(ext_nz_d)+10
                              ,prs.get('h_list', 300))
            ACTS_T          = [GAP2+HT_LST  +         25*(ind-1)     for ind in range(20)]
            ACTS_L          = [             + GAP*ind+ACTS_W*(ind-1) for ind in range(20)]
            WD_LST_MIN      = GAP*10+ACTS_W*8
            if WD_LST < WD_LST_MIN:
                ext_nz_d['Name']    = str(WD_LST_MIN-WD_LST + int(ext_nz_d['Name']))
                WD_LST              = WD_LST_MIN
            DLG_W, DLG_H    = max(WD_LST, ACTS_L[9])+GAP*3, ACTS_T[3]+3#+GAP
            ext_hnzs    = ['{}={}'.format(nm, '0' if sz[0]=='-' else sz) for (nm,sz) in ext_nz_d.items()]
            ext_vlss    = []
            for ext in self.exts:
                jext    = ext.get('jext')
                jids    = jext if jext else [ext['id']]
                jexs    = [ex for ex in self.exts if ex['id'] in jids]
                ext_vlss+=[[                                    ext['nm']
                          ,get_keys_desc('cuda_exttools,run',   ext['id'], keys)
                          ,(('>' if                             ext['shll'] else '')
                          +                                     ext['file'])        if not jext else ' ['+', '.join(ex['nm'] for ex in jexs)+']'
                          ,                                     ext['prms']         if not jext else ''
                          ,                                     ext['ddir']         if not jext else ''
                          ,                                     ext['lxrs']
                          ,                                     ext['rslt']         if not jext else ''
                          ,                                     ext['savs']
                          ]]
            pass;              #LOG and log('ext_hnzs={}',ext_hnzs)
            pass;              #LOG and log('ext_vlss={}',ext_vlss)

            ids     = [ext['id'] for ext in self.exts]
            ext     = self.exts[ext_ind] if ext_ind in range(len(self.exts)) else None
            pass;              #LOG and log('ext_ind, ext={}',(ext_ind, ext))
            
            itms    = ([(nm, '0' if sz[0]=='-' else sz) for (nm,sz) in ext_nz_d.items()], ext_vlss)
            cnts    =[dict(          tp='lb'    ,t=GAP      ,l=GAP          ,w=WD_LST           ,cap=F(_('&Tools ({})'),len(self.exts)) ) # &t
                     ,dict(cid='lst',tp='lvw'   ,t=GAP+20   ,l=GAP          ,w=4+WD_LST, h=HT_LST-20  ,items=itms                       ) #
                     ,dict(cid='edt',tp='bt'    ,t=ACTS_T[1],l=ACTS_L[1]    ,w=ACTS_W           ,cap=_('&Edit...')          ,props='1'  ) # &e  default
                     ,dict(cid='add',tp='bt'    ,t=ACTS_T[1],l=ACTS_L[2]    ,w=ACTS_W           ,cap=_('&Add...')                       ) # &a
                     ,dict(cid='jin',tp='bt'    ,t=ACTS_T[1],l=ACTS_L[3]    ,w=ACTS_W           ,cap=_('Jo&in...')  ,hint=DTLS_JOIN_H   ) # &i
                     ,dict(cid='cln',tp='bt'    ,t=ACTS_T[2],l=ACTS_L[2]    ,w=ACTS_W           ,cap=_('Clo&ne')                        ) # &n
                     ,dict(cid='del',tp='bt'    ,t=ACTS_T[2],l=ACTS_L[3]    ,w=ACTS_W           ,cap=_('&Delete...')                    ) # &d
                     ,dict(cid='up' ,tp='bt'    ,t=ACTS_T[1],l=ACTS_L[5]-AW2,w=ACTS_W           ,cap=_('&Up')       ,hint=DTLS_MVUP_H   ) # &u
                     ,dict(cid='dn' ,tp='bt'    ,t=ACTS_T[2],l=ACTS_L[5]-AW2,w=ACTS_W           ,cap=_('Do&wn')     ,hint=DTLS_MVDN_H   ) # &w
                     ,dict(cid='man',tp='bt'    ,t=ACTS_T[1],l=ACTS_L[6]    ,r=ACTS_L[7]+ACTS_W ,cap=_('Set &main for lexers...')
                                                                                                                    ,hint=DTLS_MNLX_H   ) # &m
                     ,dict(cid='mcr',tp='bt'    ,t=ACTS_T[2],l=ACTS_L[6]    ,r=ACTS_L[7]+ACTS_W ,cap=_('User macro &vars...')
                                                                                                                    ,hint=DTLS_USMS_H   ) # &v
                     ,dict(cid='adj',tp='bt'    ,t=ACTS_T[1],l=DLG_W-GAP-ACTS_W,w=ACTS_W        ,cap=_('Ad&just...'),hint=DTLS_CUST_H   ) # &j
                     ,dict(cid='-'  ,tp='bt'    ,t=ACTS_T[2],l=DLG_W-GAP-ACTS_W,w=ACTS_W        ,cap=_('Close')                         ) #
                    ]
            vals    = dict(lst=ext_ind)
            btn, vals = dlg_wrapper(_('Tools'), DLG_W, DLG_H, cnts, vals, focus_cid='lst')
            if btn is None or btn=='-':  return
            new_ext_ind = vals['lst']
            if btn=='adj':  #Custom
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

            if btn=='man':  #Main lexer tool
                self._dlg_main_tool(0 if new_ext_ind==-1 else ids[new_ext_ind])
                ext_ind     = new_ext_ind
                continue #while
            
            if btn=='mcr':  #User macros
                self._dlg_usr_mcrs()
                continue #while
            
            elif btn=='jin':
                jo_ids  = self._dlg_exts_for_join()
                if jo_ids is None or len(jo_ids)<2:
                    continue #while
                ext     = self._fill_ext({'id':gen_ext_id(self.ext4id)
                                         ,'nm':'tool{}'.format(len(self.exts))
                                         ,'jext':jo_ids
                                        })
                ed_ans      = self._dlg_config_prop(ext, keys)
                if ed_ans is None:
                    continue #while
                self.exts  += [ext]
                ids         = [ext['id'] for ext in self.exts]
                ext_ind     = len(self.exts)-1
                new_ext_ind = ext_ind           ## need?
                
            if btn=='add':
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
            
            elif btn=='edt':
                pass;          #LOG and log('?? edit self.exts[new_ext_ind]={}',self.exts[new_ext_ind])
                ed_ans  = self._dlg_config_prop(self.exts[new_ext_ind], keys)
                if ed_ans is None or not ed_ans:
                    pass;      #LOG and log('// edit self.exts[new_ext_ind]={}',self.exts[new_ext_ind])
                    continue # while
                pass;          #LOG and log('ok edit self.exts[new_ext_ind]={}',self.exts[new_ext_ind])
                
            elif btn=='up' and new_ext_ind>0: #Up
                pass;          #LOG and log('up',())
                (self.exts[new_ext_ind-1]
                ,self.exts[new_ext_ind  ])  = (self.exts[new_ext_ind  ]
                                              ,self.exts[new_ext_ind-1])
                ext_ind = new_ext_ind-1
            elif btn=='dn' and new_ext_ind<(len(self.exts)-1): #Down
                pass;          #LOG and log('dn',())
                (self.exts[new_ext_ind  ]
                ,self.exts[new_ext_ind+1])  = (self.exts[new_ext_ind+1]
                                              ,self.exts[new_ext_ind  ])
                ext_ind = new_ext_ind+1
            
            elif btn=='cln':    #Clone
                cln_ext     = copy.deepcopy(self.exts[new_ext_ind])
                cln_ext['id']= gen_ext_id(self.ext4id)
                cln_ext['nm']= cln_ext['nm']+' clone'
                self.exts   += [cln_ext]
                ext_ind     = len(self.exts)-1

            elif btn=='del':
#               if app.msg_box( 'Delete Tool\n    {}'.format(exkys[new_ext_ind])
                flds    = list(ext_nz_d.keys())
                ext_vls = ext_vlss[new_ext_ind]
                id4del  = self.exts[new_ext_ind]['id']
                jex4dl  = [ex for ex in self.exts if id4del in ex.get('jext', [])]
                if app.msg_box( _('Delete Tool?\n\n') + '\n'.join(['{}: {}'.format(flds[ind], ext_vls[ind]) 
                                                            for ind in range(len(flds))
                                                       ])
                              + ('\n\n'+'!'*50+_('\nDelete with joined Tool(s)\n   ')+'\n   '.join([ex['nm'] for ex in jex4dl]) if jex4dl else '')
                              , app.MB_YESNO)!=app.ID_YES:
                    continue # while
                for lxr in [lxr for lxr,ext_id in self.ext4lxr.items() if ext_id==id4del]:
                    del self.ext4lxr[lxr]
                del self.exts[new_ext_ind]
                for ex in jex4dl:
                    del self.exts[self.exts.index(ex)]
                    self._do_acts('delete:'+str(ex['id']), '|keys|')
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
#       focused     = 1
        DLG_W, DLG_H= GAP*3+300+400, GAP*4+300+23*2 -GAP+3
        vals    = dict(lxs=lxr_ind, tls=tool_ind)
        while True:
            lxrs_enm= ['{}{}'.format(lxr, '  >>>  {}'.format(nm4ids[self.ext4lxr[lxr]]) if lxr in self.ext4lxr else '')
                            for lxr in lxrs_l]
            cnts    =[dict(           tp='lb'   ,t=GAP+ 3           ,l=GAP          ,w=400  ,cap=_('&Lexer  >>>  main Tool')) #  &l
                     ,dict(cid='lxs' ,tp='lbx'  ,t=GAP+23   ,h=300  ,l=GAP          ,w=400  ,items=lxrs_enm                 ) #  
                     ,dict(           tp='lb'   ,t=GAP+ 3           ,l=GAP+400+GAP  ,w=300  ,cap=_('&Tools')                ) #  &t
                     ,dict(cid='tls' ,tp='lbx'  ,t=GAP+23   ,h=300  ,l=GAP+400+GAP  ,w=300  ,items=nms                      ) #  
                     ,dict(cid='set' ,tp='bt'   ,t=GAP+23+300+GAP   ,l=GAP          ,w=97   ,cap=_('&Assign Tool')          ) #  &a
                     ,dict(cid='del' ,tp='bt'   ,t=GAP+23+300+GAP   ,l=GAP+97+GAP   ,w=97   ,cap=_('&Break link')           ) #  &b
                     ,dict(cid='-'   ,tp='bt'   ,t=GAP+23+300+GAP   ,l=DLG_W-GAP-80 ,w=80   ,cap=_('Close')                 ) #  
                    ]
            btn, vals = dlg_wrapper(_('Main Tool for lexers'), DLG_W, DLG_H, cnts, vals, focus_cid='lxs')
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
        DLG_H   = GAP*2+605, GAP+20+300+GAP+25+25+3
        bt_t1   = GAP+18+300+GAP
        bt_t2   = GAP+18+300+GAP+25
        bt_l1   = GAP
        bt_l2   = GAP+120+GAP
        bt_l3   = GAP+120+GAP+120+GAP
        bt_l4   = GAP+120+GAP+120+GAP+120+GAP
        vals    = dict(lst=0)
        while True:
            itms    = (  [(_('Name'), '100'), (_('Value'),'300'), (_('Comment'),'200')]
                      , [[um['nm'],           um['ex'],           um['co']]             for um in self.umacrs] )
            cnts    =[dict(          tp='lb'    ,t=GAP         ,l=GAP          ,w=400  ,cap=_('User macro &vars')      )   # &v
                     ,dict(cid='lst',tp='lvw'   ,t=GAP+18,h=300,l=GAP          ,w=605  ,items=itms                     )   # 
                     ,dict(cid='edt',tp='bt'    ,t=bt_t1       ,l=bt_l1        ,w=120  ,cap=_('&Edit...')  ,props='1'  )   # &e  default
                     ,dict(cid='add',tp='bt'    ,t=bt_t1       ,l=bt_l2        ,w=120  ,cap=_('&Add...')               )   # &a
                     ,dict(cid='cln',tp='bt'    ,t=bt_t2       ,l=bt_l1        ,w=120  ,cap=_('Clo&ne')                )   # &n
                     ,dict(cid='del',tp='bt'    ,t=bt_t2       ,l=bt_l2        ,w=120  ,cap=_('&Delete...')            )   # &d
                     ,dict(cid='up' ,tp='bt'    ,t=bt_t1       ,l=bt_l3        ,w=120  ,cap=_('&Up')                   )   # &u
                     ,dict(cid='dn' ,tp='bt'    ,t=bt_t2       ,l=bt_l3        ,w=120  ,cap=_('Do&wn')                 )   # &w
                     ,dict(cid='evl',tp='bt'    ,t=bt_t2       ,l=bt_l4        ,w=120  ,cap=_('Eva&luate...')          )   # &v
                     ,dict(cid='-'  ,tp='bt'    ,t=bt_t2       ,l=DLG_W-GAP-80 ,w=80   ,cap=_('Close')                 )   # 
                    ]
            btn,    \
            vals    = dlg_wrapper(_('User macro vars'), DLG_W, DLG_H, cnts, vals, focus_cid='lst')
            if btn is None or btn=='-':    return
            um_ind  = vals['lst']
            if btn=='evl':
                umc_vals    = self._calc_umc_vals()
                app.dlg_menu(app.MENU_LIST_ALT, '\n'.join(
                    ['{}: {}\t{}'.format(umc['nm'], umc['ex'], umc_vals[umc['nm']]) for umc in self.umacrs]
                ))

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
                    um_btn, \
                    umc     = dlg_wrapper(_('Edit user macro var'), GAP+400+GAP, GAP+135+GAP, um_cnts, umc, focus_cid=um_fcsd)
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
                                ,_('Comment: {}').format(self.umacrs[um_ind]['co'])]), app.MB_YESNO)!=app.ID_YES:
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
        vals    = dlg_wrapper(_('Select Tools for join'), GAP+300+GAP, GAP+400+GAP+24+GAP, cnts, vals, focus_cid='exs')
        if btn is None or btn=='-': return None
        crt,sels= vals['exs']
        ext_ids = [ext4jn[ind]['id'] for ind in range(len(sels)) if sels[ind]=='1']
        return ext_ids
       #def _dlg_exts_for_join
        
    def _dlg_config_prop(self, src_ext, keys=None, for_ed='1'):
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
        DLG_W, DLG_H    = PRP3_L+PRP3_W+GAP, PROP_T[17]-21
        
        jex_ids         = ed_ext.get('jext', None)
        joined          = jex_ids is not None
        sel_jext        = 0
        focus_cid   = 'nm'
        while True:
            ed_kys  = get_keys_desc('cuda_exttools,run', ed_ext['id'], keys)
            val_savs= self.savs_vals.index(ed_ext['savs']) if ed_ext is not None else 0
            val_rslt= self.rslt_vals.index(ed_ext['rslt']) if ed_ext is not None else 0
            
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
            cnts    = ([]
                     +[dict(           tp='lb'   ,tid='nm'      ,l=PRP1_L   ,w=PRP1_W   ,cap=_('&Name')                         )] # &n
                     +[dict(cid='nm'  ,tp='ed'   ,t=PROP_T[1]   ,l=PRP2_L   ,w=PRP2_W                                           )] #
                    +([]                                       
                     +[dict(           tp='lb'   ,tid='seri'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Se&ries')                       )] # &r
                     +[dict(cid='seri',tp='lbx'  ,t=PROP_T[2]   ,l=PRP2_L   ,w=PRP2_W    ,b=PROP_T[6]-GAP,items=jext_nms        )] #
                     +[dict(cid='?ser',tp='bt'   ,t=PROP_T[2]   ,l=PRP3_L   ,w=PRP3_W   ,cap=_('&Select...')    ,en=for_ed      )] # &s
                     +[dict(cid='view',tp='bt'   ,t=PROP_T[3]-4 ,l=PRP3_L   ,w=PRP3_W   ,cap=_('Vie&w...')      ,en=for_ed      )] # &w
                     +[dict(cid='up'  ,tp='bt'   ,t=PROP_T[4]+2 ,l=PRP3_L   ,w=PRP3_W   ,cap=_('&Up')           ,en=for_ed      )] # &u
                     +[dict(cid='dn'  ,tp='bt'   ,t=PROP_T[5]-2 ,l=PRP3_L   ,w=PRP3_W   ,cap=_('&Down')         ,en=for_ed      )] # &d
                    if joined else []
                     +[dict(           tp='lb'   ,tid='file'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('&File name')                    )] # &f
                     +[dict(cid='file',tp='ed'   ,t=PROP_T[2]   ,l=PRP2_L   ,w=PRP2_W                                           )] #
                     +[dict(cid='?fil',tp='bt'   ,tid='file'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('&Browse...')    ,en=for_ed      )] # &b
                     +[dict(cid='shll',tp='ch'   ,t=PROP_T[3]-2 ,l=PRP2_L   ,w=PRP2_W   ,cap=_('&Shell command'),en=for_ed      )] # &s
                                                 
                     +[dict(           tp='lb'   ,tid='prms'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('&Parameters')                   )] # &p
                     +[dict(cid='prms',tp='ed'   ,t=PROP_T[4]   ,l=PRP2_L   ,w=PRP2_W                                           )] #
                     +[dict(cid='?mcr',tp='bt'   ,tid='prms'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('A&dd...')       ,en=for_ed      )] # &a
                                                 
                     +[dict(           tp='lb'   ,tid='ddir'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('&Initial folder')               )] # &i
                     +[dict(cid='ddir',tp='ed'   ,t=PROP_T[5]   ,l=PRP2_L   ,w=PRP2_W                                           )] #
                     +[dict(cid='?dir',tp='bt'   ,tid='ddir'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('B&rowse...')    ,en=for_ed      )] # &r
                    )
                     +[dict(           tp='lb'   ,tid='lxrs'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Lexers')                        )] #
                     +[dict(cid='lxrs',tp='ed'   ,t=PROP_T[6]   ,l=PRP2_L   ,w=PRP2_W                       ,props='1,0,1'      )] #     ro,mono,border
                     +[dict(cid='?lxr',tp='bt'   ,tid='lxrs'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('Le&xers...')    ,en=for_ed      )] # &x
                                                 
                     +[dict(           tp='lb'   ,tid='main'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Main for')                      )] #
                     +[dict(cid='main',tp='ed'   ,t=PROP_T[7]   ,l=PRP2_L   ,w=PRP2_W                       ,props='1,0,1'      )] #     ro,mono,border
                     +[dict(cid='?man',tp='bt'   ,tid='main'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('Set &main...')  ,en=for_ed      )] # &m
                                                 
                     +[dict(           tp='lb'   ,tid='savs'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Sa&ve before')                  )] # &v
                     +[dict(cid='savs',tp='cb-ro',t=PROP_T[8]   ,l=PRP2_L   ,w=PRP2_W   ,items=self.savs_caps   ,en=for_ed      )] #
                                              
                     +[dict(           tp='lb'   ,tid='keys'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Hotkey')                        )] #
                     +[dict(cid='keys',tp='ed'   ,t=PROP_T[9]   ,l=PRP2_L   ,w=PRP2_W                       ,props='1,0,1'      )] #     ro,mono,border
                     +[dict(cid='?key',tp='bt'   ,tid='keys'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('Assi&gn...')    ,en=for_ed      )] # &g
                    +([] if joined else []                     
                     +[dict(           tp='lb'   ,tid='rslt'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('&Capture output')               )] # &c
                     +[dict(cid='rslt',tp='cb-ro',t=PROP_T[11]  ,l=PRP2_L   ,w=PRP2_W   ,items=self.rslt_caps   ,en=for_ed      )] 
                     +[dict(           tp='lb'   ,tid='encd'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Encoding')                      )] #
                     +[dict(cid='encd',tp='ed'   ,t=PROP_T[12]  ,l=PRP2_L   ,w=PRP2_W                       ,props='1,0,1'      )] #     ro,mono,border
                     +[dict(cid='?enc',tp='bt'   ,tid='encd'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('S&elect...')    ,en=for_ed      )] # &
                     +[dict(           tp='lb'   ,tid='pttn'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Pattern')                       )] #
                     +[dict(cid='pttn',tp='ed'   ,t=PROP_T[13]  ,l=PRP2_L   ,w=PRP2_W                       ,props='1,0,1'      )] #     ro,mono,border
                     +[dict(cid='?ptn',tp='bt'   ,tid='pttn'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('Se&t...')       ,en=for_ed      )] # &e
                    )                                         
                     +[dict(           tp='lb'   ,tid='more'    ,l=PRP1_L   ,w=PRP1_W   ,cap=_('Advanced')                      )] #
                     +[dict(cid='more',tp='ed'   ,t=PROP_T[14]  ,l=PRP2_L   ,w=PRP2_W                       ,props='1,0,1'      )] #     ro,mono,border
                     +[dict(cid='?mor',tp='bt'   ,tid='more'    ,l=PRP3_L   ,w=PRP3_W   ,cap=_('Set...')        ,en=for_ed      )] #
                    +([] if joined else []                     
                     +[dict(cid='help',tp='bt'   ,t=PROP_T[15]+9,l=GAP      ,w=PRP3_W       ,cap=_('Help')      ,en=for_ed      )] #
                    )                                         
                     +[dict(cid='!'   ,tp='bt'   ,t=PROP_T[15]+9,l=DLG_W-GAP*2-100*2,w=100  ,cap=_('OK')    ,props='1',en=for_ed)] #     default
                     +[dict(cid='-'   ,tp='bt'   ,t=PROP_T[15]+9,l=DLG_W-GAP*1-100*1,w=100  ,cap=_('Cancel')                    )] #
                    )
            btn,    \
            vals    = dlg_wrapper(_('Tool properties'), DLG_W, DLG_H, cnts, vals, focus_cid=focus_cid)
            if btn is None or btn=='-': return None
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
                    focus_cid   = 'nm'      #focused = 1
                    continue #while
                elif not joined and not ed_ext['file']:
                    app.msg_box(_('Set File name'), app.MB_OK)
                    focus_cid   = 'file'    #focused = 3
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
                EXT_HELP_BODY   = \
_('''In Tool properties
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
   {InteractiveFile}  - File name will be asked''')
                dlg_wrapper(_('Tool macros'), GAP*2+550, GAP*3+25+450,
                     [dict(cid='htx',tp='me'    ,t=GAP  ,h=450  ,l=GAP          ,w=550  ,props='1,1,1' ) #  ro,mono,border
                     ,dict(cid='-'  ,tp='bt'    ,t=GAP+450+GAP  ,l=GAP+550-90   ,w=90   ,cap='&Close'  )
                     ], dict(htx=EXT_HELP_BODY), focus_cid='htx')
                continue #while

            if joined and btn=='view' and sel_jext!=-1: # View one of joined
                self._dlg_config_prop(self.ext4id[str(jex_ids[sel_jext])], keys, for_ed='0')
            
            if joined and btn=='?ser': # Select exts to join
                jex_ids_new = self._dlg_exts_for_join(jex_ids)
                if jex_ids_new is not None and len(jex_ids_new)>1:
                    jex_ids = ed_ext['jext'] = jex_ids_new
                continue #while

            if joined and btn==  'up' and sel_jext>0:
                (jex_ids[sel_jext-1] 
                ,jex_ids[sel_jext  ])   =   (jex_ids[sel_jext  ] 
                                            ,jex_ids[sel_jext-1])
                sel_jext               -= 1
            if joined and btn=='down' and sel_jext<len(jex_ids):
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
                    ed_ext['file'] = file4run
            
            elif btn=='?dir':
                file4dir= app.dlg_file(True, '!', ed_ext['ddir'], '')   # '!' to disable check "filename exists"
                if file4dir is not None:
                    ed_ext['ddir'] = os.path.dirname(file4dir)

            elif btn=='?mcr':   #Append param {*}
                ed_ext['prms']  = append_prmt(ed_ext['prms'], self.umacrs)

            elif btn=='?key':
                app.dlg_hotkeys('cuda_exttools,run,'+str(ed_ext['id']))
                keys    = apx._json_loads(open(keys_json).read()) if os.path.exists(keys_json) else {}
            
            elif btn=='?lxr':   #Lexers only
                lxrs    = ','+ed_ext['lxrs']+','
                lxrs_l  = _get_lexers()
                sels    = ['1' if ','+lxr+',' in lxrs else '0' for lxr in lxrs_l]
                crt     = str(sels.index('1') if '1' in sels else 0)

                lx_cnts =[dict(cid='lxs',tp='ch-lbx',t=GAP,h=400    ,l=GAP          ,w=200  ,items=lxrs_l           ) #
                         ,dict(cid='!'  ,tp='bt'    ,t=GAP+400+GAP  ,l=    200-140  ,w=70   ,cap=_('OK'),props='1'  ) #  default
                         ,dict(cid='-'  ,tp='bt'    ,t=GAP+400+GAP  ,l=GAP+200- 70  ,w=70   ,cap=_('Cancel')        ) #  
                        ]
                lx_vals = dict(lxs=(crt,sels))
                lx_btn, \
                lx_vals = dlg_wrapper(_('Select lexers'), GAP+200+GAP, GAP+400+GAP+24+GAP, lx_cnts, lx_vals, focus_cid='lxs')
                if lx_btn=='!':
                    crt,sels= lx_vals['lxs']
                    lxrs    = [lxr for (ind,lxr) in enumerate(lxrs_l) if sels[ind]=='1']
                    ed_ext['lxrs'] = ','.join(lxrs)
            
            elif btn=='?enc':
                enc_nms = get_encoding_names()
                enc_ind = app.dlg_menu(app.MENU_LIST_ALT, '\n'.join(enc_nms))
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
                     dict(           tp='lb',t=GAP+i*50     ,l=GAP          ,w=500  ,cap=F('("{}") {}', ad_key, a['cap']),hint=a['hnt'] )
                    ,dict(cid=ad_key,tp='ed',t=GAP+i*50+18  ,l=GAP          ,w=500                                                      )
                          ]
                   #for (i, a)
                avd_h   = len(ADV_PROPS)*50
                ad_cnts   += [
                     dict(cid='!'   ,tp='bt',t=GAP+avd_h+GAP,l=    500-140  ,w=70   ,cap=_('OK')     ,props='1'                         ) # default
                    ,dict(cid='-'   ,tp='bt',t=GAP+avd_h+GAP,l=GAP+500- 70  ,w=70   ,cap=_('Cancel')                                    )
                            ]
                ad_btn, \
                ad_vals = dlg_wrapper(_('Advanced properties'), GAP+500+GAP, GAP+avd_h+GAP+24+GAP+3, ad_cnts, ad_vals, focus_cid='-')
                if ad_btn is None or ad_btn=='-':   continue#while
                for a in enumerate(ADV_PROPS):
                    if ad_vals[a['key']]==a['def']:
                        ed_ext.pop(a['key'], None)
                    else:
                        ed_ext[    a['key']]= ad_vals[a['key']]
                   #for a
           #while True
       #def _dlg_config_prop

    def _dlg_pattern(self, pttn_re, pttn_test, run_nm):
        pass;                  #LOG and log('pttn_re, pttn_test={}',(pttn_re, pttn_test))
        grp_dic = {}
        if pttn_re and pttn_test:
            grp_dic = re.search(pttn_re, pttn_test).groupdict('') if re.search(pttn_re, pttn_test) is not None else {}
        
        RE_REF  = 'https://docs.python.org/3/library/re.html'
        DLG_W,  \
        DLG_H   = GAP+550+GAP, GAP+250+3#+GAP
        cnts    =[dict(cid=''          ,tp='ln-lb'  ,t=GAP          ,l=GAP              ,w=300              ,cap=_('&Regular expression')
                                                                                                            ,props=RE_REF                ) # &r
                 ,dict(cid='pttn_re'   ,tp='ed'     ,t=GAP+18       ,l=GAP              ,r=DLG_W-GAP*2-70                                ) #
                 ,dict(cid='apnd'      ,tp='bt'     ,tid='pttn_re'  ,l=DLG_W-GAP*1-70   ,w=70               ,cap=_('&Add...')
                                                                                                            ,hint='Append named group'   ) # &a
#                ,dict(cid='help'      ,tp='bt'     ,tid='pttn_re'  ,l=DLG_W-GAP*1-70   ,w=70               ,cap='&?..'                  ) # &?
                 # Testing                                                                                         
                 ,dict(cid=''          ,tp='lb'     ,t= 60          ,l=GAP              ,w=300              ,cap=_('Test "&Output line"')) # &o
                 ,dict(cid='pttn_test' ,tp='ed'     ,t= 60+18       ,l=GAP              ,r=DLG_W-GAP*2-70                                ) #
                 ,dict(cid='test'      ,tp='bt'     ,tid='pttn_test',l=DLG_W-GAP*1-70   ,w=70               ,cap=_('&Test')              ) # &t
                                                                                                                               
                 ,dict(cid=''          ,tp='lb'     ,t=110+GAP*0+23*0   ,l=GAP+ 80      ,w=300              ,cap=_('Testing results')    ) #
                 ,dict(cid=''          ,tp='lb'     ,tid='file'         ,l=GAP          ,w=80               ,cap=_('Filename')           ) #
                 ,dict(cid='file'      ,tp='ed'     ,t=110+GAP*0+23*1   ,l=GAP+ 80      ,r=DLG_W-GAP*2-70               ,props='1,0,1'   ) #   ro,mono,border
                 ,dict(cid=''          ,tp='lb'     ,tid='line'         ,l=GAP          ,w=80               ,cap=_('Line')               ) #
                 ,dict(cid='line'      ,tp='ed'     ,t=110+GAP*1+23*2   ,l=GAP+ 80      ,r=DLG_W-GAP*2-70               ,props='1,0,1'   ) #   ro,mono,border
                 ,dict(cid=''          ,tp='lb'     ,tid='col'          ,l=GAP          ,w=80               ,cap=_('Column')             ) #
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
            vals    = dlg_wrapper(_('Tool "{}" output pattern').format(run_nm), DLG_W, DLG_H, cnts, vals, focus_cid='pttn_re')
            if btn is None or btn=='cancel':    return (None, None)
            pttn_re = vals['pttn_re']
            pttn_test=vals['pttn_test']

            if False:pass
            elif btn == 'ok':
                return (pttn_re, pttn_test)
            
            elif btn == 'apnd':
                grps    = [['(?P<file>)' , 'Filename (default - current file name)']
                          ,['(?P<line>)' , 'Number of line (default - 1)']
                          ,['(?P<col>)'  , 'Number of column (default - 1)']
                          ,['(?P<line0>)', 'Number of line (0-based, default - 0)']
                          ,['(?P<col0>)' , 'Number of column (0-based, default - 0)']
                        ]
                grp_i   = app.dlg_menu(app.MENU_LIST_ALT, '\n'.join(['\t'.join(g) for g in grps]))
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
                grp_dic = re.search(pttn_re, pttn_test).groupdict('') if re.search(pttn_re, pttn_test) is not None else {}
            
            elif btn == 'load':
                ps_nms  = ['{}\t{}'.format(ps['name'], ps['run']) for ps in self.preset]
                ps_ind  = app.dlg_menu(app.MENU_LIST, '\n'.join(ps_nms))
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
        ext['ddir'] = ext.get('ddir', '')
        ext['shll'] = ext.get('shll', 'N')=='Y' if str(ext.get('shll', 'N'))    in 'NY'            else ext.get('shll', False)
        ext['prms'] = ext.get('prms', '')
        ext['savs'] = ext.get('savs', SAVS_N)
        ext['rslt'] = ext.get('rslt', RSLT_N)   if     ext.get('rslt', RSLT_N)  in self.rslt_vals  else RSLT_N
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
            umc_vals[umc['nm']]  = _subst_props(umc['ex'], file_nm, umcs=umc_vals)
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

def _subst_props(prm, file_nm, cCrt=-1, rCrt=-1, ext_nm='', umcs={}):
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
        
    if '{' not in prm:  return prm
    for umc_k,umc_v in umcs.items():
        prm = prm.replace(umc_k, umc_v)
        if '{' not in prm:  return prm
        
    return prm
   #def _subst_props

def append_prmt(tostr, umacrs, excl_umc=None):
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
    prms_l +=['{}\t{}'.format(umc['nm'], umc['ex']) 
                for umc in umacrs 
                if (excl_umc is None or umc['nm']!=excl_umc)]
                        
    prm_i   = app.dlg_menu(app.MENU_LIST_ALT, '\n'.join(prms_l))
    if prm_i is not None:
        tostr  = (tostr + (' '+prms_l[prm_i].split('\t')[0])).lstrip()
    return tostr
   #def append_prmt

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
'''
