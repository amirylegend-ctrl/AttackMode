# AttackMode
import datetime
from babase import Plugin
from bauiv1 import (
    containerwidget as cw,
    screenmessage as push,
    textwidget as tw,
    buttonwidget as bw,
    gettexture as gt,
    apptimer as teck,
    getsound as gs,
    app as APP,
    CallStrict,
    CallPartial,
    scrollwidget as sw,
    columnwidget as clw
)
from bascenev1 import (
    get_chat_messages as GCM,
    chatmessage as CM,
    get_game_roster,
    disconnect_client
)

MASTER_ACCOUNT = "TAHARI1"
EXPIRY_DATE = "2026-02-28"

attack_targets = {} 
pr = 'att_'

def var(s, v=None):
    c = APP.config
    s = pr + s
    if v is None:
        return c.get(s, v)
    c[s] = v
    c.commit()
def get_account_name_from_game():
    try:
        if hasattr(APP, 'plus') and hasattr(APP.plus, 'get_v1_account_state'):
            account_state = APP.plus.get_v1_account_state()
            if account_state == 'signed_in' and hasattr(APP.plus, 'get_v1_account_name'):
                account_name = APP.plus.get_v1_account_name()
                if account_name and str(account_name).strip():
                    return str(account_name).strip()
        try:
            account_name = APP.config.get('Player Name', '')
            if account_name and str(account_name).strip():
                return str(account_name).strip()
        except:
            pass
        return None
    except Exception as e:
        print(f"AttackMode: Error getting account name: {e}")
        return None

def check_expiry_date():
    try:
        expiry = datetime.datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date()
        today = datetime.datetime.now().date()
        return today > expiry
    except Exception as e:
        print(f"AttackMode: Error checking expiry date: {e}")
        return False

def show_expiry_notification():
    push("⛔ تاریخ انقضا Attack Mode به پایان رسید", color=(1, 0, 0))
    push(f"تاریخ انقضا: {EXPIRY_DATE}", color=(1, 0.5, 0))
    gs('error').play()

def show_unauthorized_notification(current_account):
    push("🚫 اکانت غیرمجاز برای Attack Mode", color=(1, 0, 0))
    push(f"این پلاگین فقط برای اکانت '{MASTER_ACCOUNT}' فعال است", color=(1, 0.5, 0))
    push(f"اکانت فعلی: {current_account}", color=(1, 1, 0.5))
    gs('shieldDown').play()

def auto_detect_owner_on_start():
    """تشخیص خودکار owner از حساب بازی (اگر قبلاً تنظیم نشده باشد)"""
    current_owner = var('owner_account')
    if not current_owner:
        try:
            account_name = get_account_name_from_game()
            if account_name and str(account_name).strip():
                var('owner_account', str(account_name).strip())
                print(f"AttackMode: Auto-detected owner account: {account_name}")
                return True
        except Exception as e:
            print(f"AttackMode: Error auto-detecting owner: {e}")
    return False

def is_owner(sender_name):
    """بررسی مالکیت با استفاده از تنظیمات owner (ذخیره شده با پیشوند att_)"""
    owner_account = var('owner_account')
    owner_nickname = var('owner_nickname')
    if not owner_account and not owner_nickname:
        return False
    if owner_nickname and sender_name == owner_nickname:
        return True
    if owner_account:
        try:
            roster = get_game_roster()
            for client in roster:
                if 'players' in client and client['players']:
                    for p in client['players']:
                        if p.get('name', '') == sender_name:
                            device_name = client.get('display_string', '')
                            if owner_account.lower() in device_name.lower():
                                return True
        except:
            pass
    return False
def find_client_id_by_name(name):
    try:
        roster = get_game_roster()
        for client in roster:
            if 'players' in client and client['players']:
                for p in client['players']:
                    if p.get('name', '').strip() == name.strip():
                        return client.get('client_id')
                    display = client.get('display_string', '')
                    if display and display.strip() == name.strip():
                        return client.get('client_id')
    except Exception as e:
        print(f"AttackMode: Error finding client: {e}")
    return None

def is_player_present(client_id):
    try:
        roster = get_game_roster()
        for client in roster:
            if client.get('client_id') == client_id:
                return True
    except:
        pass
    return False
def stop_attack(target_id):
    if target_id in attack_targets:
        data = attack_targets[target_id]
        if data.get('timer'):
            try:
                data['timer'].cancel()
            except:
                pass
        data['active'] = False
        del attack_targets[target_id]

def start_attack(target_name):
    global attack_targets
    target_id = find_client_id_by_name(target_name)
    if not target_id:
        SC.err(f'Player "{target_name}" not found!')
        return

    if target_id in attack_targets:
        stop_attack(target_id)

    commands = var('attack_commands') or []
    delays = var('attack_delays') or []
    loop_delay = var('attack_loop_delay') or 30.0

    if not commands:
        SC.err('No attack commands set! Configure in Attack Settings.')
        return

    attack_targets[target_id] = {
        'name': target_name,
        'commands': commands,
        'delays': delays,
        'loop_delay': loop_delay,
        'active': True,
        'paused': False,
        'index': 0,
        'timer': None,
        'target_id': target_id
    }

    send_next_attack(target_id)
    push(f'⚔️ Attack started on {target_name}', color=(1, 0.5, 0))

def send_next_attack(target_id):
    """ارسال پیام بعدی در حلقه حمله"""
    if target_id not in attack_targets:
        return

    data = attack_targets[target_id]
    if not data['active']:
        return

    if data.get('paused', False):
        return

    if not is_player_present(target_id):
        data['paused'] = True
        push(f'⚠️ {data["name"]} فرار کرد؟ دوباره ببینمش جرش میدم!', color=(1, 0, 0))
        return

    idx = data['index']
    commands = data['commands']
    delays = data['delays']
    loop_delay = data['loop_delay']

    if idx >= len(commands):
        idx = 0
        data['index'] = 0

    cmd = commands[idx]
    delay = delays[idx] if idx < len(delays) else 0
    response = f'%{cmd} {target_id}'
    safe_send_message(response)

    next_idx = idx + 1
    if next_idx >= len(commands):
        next_delay = loop_delay
        next_idx = 0
    else:
        next_delay = delays[next_idx]

    data['index'] = next_idx

    from babase import apptimer
    timer = apptimer(next_delay, CallStrict(send_next_attack, target_id))
    data['timer'] = timer
_ignore_messages = []

def safe_send_message(message):
    global _ignore_messages
    _ignore_messages.append(message)
    if len(_ignore_messages) > 10:
        _ignore_messages.pop(0)
    CM(message)
    print(f"AttackMode: Sent message (added to ignore list): {message}")

def check_paused_targets():
    """بررسی دوره‌ای بازیکنانی که موقتاً خارج شده‌اند"""
    for target_id, data in list(attack_targets.items()):
        if data.get('paused', False) and data.get('active', False):
            if is_player_present(target_id):
                data['paused'] = False
                push(f'✅ {data["name"]} برگشت! ادامه حمله.', color=(0, 1, 0))
                send_next_attack(target_id)
    from babase import apptimer
    apptimer(5, check_paused_targets)
class SC:
    @classmethod
    def UIS(cls):
        i = APP.ui_v1.uiscale
        if i == 0:
            return 1.5
        elif i == 1:
            return 1.1
        else:
            return 0.8

    @classmethod
    def bw(cls, **k):
        kwargs = dict(k)
        if 'textcolor' not in kwargs:
            kwargs['textcolor'] = (1, 1, 1)
        if 'enable_sound' not in kwargs:
            kwargs['enable_sound'] = False
        if 'button_type' not in kwargs:
            kwargs['button_type'] = 'square'
        if 'color' not in kwargs:
            kwargs['color'] = (0.18, 0.18, 0.18)
        return bw(**kwargs)

    @classmethod
    def cw(cls, source, ps=0, **k):
        from bauiv1 import get_special_widget as gsw
        o = source.get_screen_space_center() if source else None
        kwargs = dict(k)
        filtered_kwargs = {}
        for key, value in kwargs.items():
            if key not in ['parent', 'scale_origin_stack_offset', 'scale', 'transition', 'color']:
                filtered_kwargs[key] = value
        r = cw(
            parent=gsw('overlay_stack'),
            scale_origin_stack_offset=o,
            scale=cls.UIS() + ps,
            transition='in_scale',
            color=(0.18, 0.18, 0.18),
            **filtered_kwargs
        )
        cw(r, on_outside_click_call=CallPartial(cls.swish, t=r))
        return r

    @classmethod
    def swish(cls, t=None):
        gs('swish').play()
        if t:
            cw(t, transition='out_scale')

    @classmethod
    def err(cls, t):
        gs('block').play()
        push(t, color=(1, 1, 0))

    @classmethod
    def ok(cls):
        gs('dingSmallHigh').play()
        push('Success!', color=(0, 1, 0))

class AttackSettingsPanel:
    def __init__(self, source):
        if hasattr(self, 'w') and self.w:
            try:
                SC.swish(self.w)
            except:
                pass

        w = self.w = SC.cw(
            source=source,
            size=(450, 400),
            ps=SC.UIS() * 0.8
        )
        tw(
            parent=w,
            text='⚔️ Attack Mode Settings',
            scale=1.2,
            position=(210, 370),
            h_align='center',
            color=(1, 0.5, 0)
        )

        tw(parent=w, text='Commands & Delays:', position=(20, 330), color=(0.8, 0.8, 1))

        self.scroll = sw(
            parent=w,
            size=(410, 220),
            position=(20, 100),
            color=(0.1, 0.1, 0.1),
            highlight=False
        )
        self.column = clw(parent=self.scroll, left_border=10, top_border=10, bottom_border=10)

        self.commands = var('attack_commands') or []
        self.delays = var('attack_delays') or []
        self.loop_delay = var('attack_loop_delay') or 30.0

        self.rows = []
        self._rebuild_rows()

        SC.bw(
            parent=w,
            label='➕ Add Row',
            size=(100, 30),
            position=(20, 70),
            on_activate_call=CallStrict(self._add_row)
        )

        tw(parent=w, text='Loop Delay (s):', position=(20, 40), color=(0.8, 1, 0.8))
        self.loop_entry = tw(
            parent=w,
            text=str(self.loop_delay),
            size=(80, 30),
            editable=True,
            position=(140, 38),
            v_align='center',
            color=(0.8, 1, 0.8)
        )

        SC.bw(
            parent=w,
            label='💾 Save',
            size=(80, 35),
            position=(350, 35),
            on_activate_call=CallStrict(self._save),
            color=(0, 0.6, 0)
        )

        SC.swish()

    def _rebuild_rows(self):
        for child in self.column.get_children():
            child.delete()
        header = cw(parent=self.column, size=(390, 25), background=False)
        tw(parent=header, text='Command', position=(10, 0), color=(1, 1, 0.5))
        tw(parent=header, text='Delay (s)', position=(200, 0), color=(1, 1, 0.5))
        self.rows = []
        for i in range(len(self.commands)):
            self._add_row_widgets(i)

    def _add_row_widgets(self, i):
        row = cw(parent=self.column, size=(390, 35), background=False)
        cmd_entry = tw(
            parent=row,
            text=self.commands[i] if i < len(self.commands) else '',
            size=(150, 30),
            editable=True,
            position=(10, 2),
            v_align='center',
            color=(0.8, 0.8, 1)
        )
        delay_entry = tw(
            parent=row,
            text=str(self.delays[i]) if i < len(self.delays) else '0',
            size=(80, 30),
            editable=True,
            position=(180, 2),
            v_align='center',
            color=(1, 0.8, 0.8)
        )
        del_btn = SC.bw(
            parent=row,
            label='❌',
            size=(25, 25),
            position=(280, 5),
            on_activate_call=CallStrict(self._delete_row, i),
            textcolor=(1, 0, 0)
        )
        self.rows.append((row, cmd_entry, delay_entry, del_btn))

    def _add_row(self):
        self.commands.append('')
        self.delays.append(0.0)
        self._add_row_widgets(len(self.commands) - 1)

    def _delete_row(self, index):
        if 0 <= index < len(self.rows):
            row, _, _, _ = self.rows.pop(index)
            row.delete()
            self.commands.pop(index)
            self.delays.pop(index)
            for i, (r, cmd, delay, btn) in enumerate(self.rows):
                btn.on_activate_call = CallStrict(self._delete_row, i)

    def _save(self):
        new_commands = []
        new_delays = []
        for _, cmd_entry, delay_entry, _ in self.rows:
            cmd = tw(query=cmd_entry).strip()
            if not cmd:
                continue
            try:
                delay = float(tw(query=delay_entry).strip())
                if delay < 0:
                    delay = 0
            except:
                delay = 0
            new_commands.append(cmd.lower())
            new_delays.append(delay)

        try:
            loop = float(tw(query=self.loop_entry).strip())
            if loop < 0:
                loop = 30
        except:
            loop = 30

        var('attack_commands', new_commands)
        var('attack_delays', new_delays)
        var('attack_loop_delay', loop)

        SC.ok()
        push('⚔️ Attack settings saved!', color=(0, 1, 0))
        SC.swish(self.w)

class AttackListPanel:
    def __init__(self, source):
        if hasattr(self, 'w') and self.w:
            try:
                SC.swish(self.w)
            except:
                pass

        w = self.w = SC.cw(
            source=source,
            size=(500, 400),
            ps=SC.UIS() * 0.8
        )
        tw(
            parent=w,
            text='⚔️ Active Attacks',
            scale=1.2,
            position=(230, 370),
            h_align='center',
            color=(1, 0.5, 0)
        )

        if not attack_targets:
            tw(parent=w, text='No active attacks.', position=(200, 200), color=(0.8, 0.8, 0.8))
            SC.swish()
            return

        header = cw(parent=w, size=(460, 30), position=(20, 310), background=False)
        tw(parent=header, text='Player', position=(10, 0), color=(1, 1, 0.5))
        tw(parent=header, text='Status', position=(200, 0), color=(1, 1, 0.5))
        tw(parent=header, text='Actions', position=(350, 0), color=(1, 1, 0.5))

        scroll = sw(
            parent=w,
            size=(460, 260),
            position=(20, 40),
            color=(0.1, 0.1, 0.1),
            highlight=False
        )
        column = clw(parent=scroll, left_border=10, top_border=10, bottom_border=10)

        for target_id, data in list(attack_targets.items()):
            row = cw(parent=column, size=(440, 35), background=False)
            tw(parent=row, text=data['name'], position=(10, 7), color=(0.8, 1, 0.8), maxwidth=150)
            if data.get('paused', False):
                status = '⏸️ Paused (left)'
                status_color = (1, 0.8, 0)
            elif data.get('active', False):
                status = '▶️ Running'
                status_color = (0, 1, 0)
            else:
                status = '⏹️ Stopped'
                status_color = (0.8, 0.8, 0.8)
            tw(parent=row, text=status, position=(200, 7), color=status_color)
            SC.bw(
                parent=row,
                label='⏹️ Stop',
                size=(60, 25),
                position=(350, 5),
                on_activate_call=CallStrict(self._stop_attack, target_id),
                color=(0.8, 0, 0)
            )

        SC.swish()

    def _stop_attack(self, target_id):
        stop_attack(target_id)
        SC.ok()
        push(f'Attack on {attack_targets.get(target_id, {}).get("name", "unknown")} stopped.', color=(1, 0.5, 0))
        if hasattr(self, 'w') and self.w:
            SC.swish(self.w)
            teck(0.1, CallStrict(self.__init__, self.w))

class OwnerSettingsPanel:
    def __init__(self, source):
        if hasattr(self, 'w') and self.w:
            try:
                SC.swish(self.w)
            except:
                pass

        self.source = source
        w = self.w = SC.cw(
            source=source,
            size=(350, 320),
            ps=SC.UIS() * 0.8
        )
        tw(
            parent=w,
            text='Attack Mode Owner Settings',
            scale=0.9,
            position=(155, 290),
            h_align='center',
            color=(1, 0.5, 0)
        )
        owner_account = var('owner_account') or ''
        owner_nickname = var('owner_nickname') or ''
        owner_client_id = var('owner_client_id') or ''

        tw(parent=w, text='Account:', scale=0.9, position=(10, 270), color=(0.8, 1, 0))
        tw(parent=w, text=owner_account if owner_account else 'Not set', scale=0.9,
           position=(100, 270), color=(0.8, 1, 0.8) if owner_account else (1, 0.8, 0.8))

        if owner_client_id:
            tw(parent=w, text=f'ID: {owner_client_id}', position=(10, 250), scale=0.8, color=(1, 1, 0.8))
        if owner_nickname and owner_nickname != owner_account:
            tw(parent=w, text=f'Nickname: {owner_nickname}', position=(10, 230), scale=0.8, color=(1, 0.8, 0.8))

        tw(parent=w, text='Auto Detection:', position=(10, 200), scale=0.9, color=(0.8, 0.8, 1))
        y_pos = 170
        SC.bw(
            parent=w,
            label='Get My Account',
            size=(160, 35),
            position=(10, y_pos),
            on_activate_call=CallStrict(self._get_game_account)
        )
        SC.bw(
            parent=w,
            label='Detect Nickname',
            size=(160, 35),
            position=(180, y_pos),
            on_activate_call=CallStrict(self._detect_from_players)
        )
        y_pos -= 50
        SC.bw(
            parent=w,
            label='Detect from Chat',
            size=(160, 35),
            position=(10, y_pos),
            on_activate_call=CallStrict(self._detect_from_chat)
        )
        y_pos -= 50
        tw(parent=w, text='Manual:', position=(10, y_pos), scale=0.8, color=(0, 0.9, 0.7))
        self.manual_input = tw(
            parent=w,
            maxwidth=200,
            size=(200, 30),
            editable=True,
            v_align='center',
            color=(0, 0.9, 0.7),
            position=(90, y_pos - 5),
            allow_clear_button=False,
            text=owner_account if owner_account else ''
        )
        y_pos -= 35
        SC.bw(
            parent=w,
            label='Set Manual',
            size=(100, 35),
            color=(0, 0.6, 0),
            position=(230, y_pos),
            on_activate_call=CallStrict(self._set_manual)
        )
        SC.bw(
            parent=w,
            label='Clear',
            size=(100, 35),
            color=(1, 0, 0),
            position=(30, y_pos),
            on_activate_call=CallStrict(self._clear_owner)
        )

        SC.swish()

    def _get_game_account(self):
        try:
            account_name = get_account_name_from_game()
            if account_name:
                var('owner_account', account_name)
                SC.ok()
                push(f'Owner account set to: {account_name}', color=(0, 1, 0))
                self._refresh_panel()
            else:
                SC.err('Could not get account name from game.')
        except Exception as e:
            SC.err(f'Error: {str(e)}')

    def _detect_from_players(self):
        try:
            roster = get_game_roster()
            players = []
            for client in roster:
                if 'players' in client and client['players']:
                    for p in client['players']:
                        players.append({
                            'name': p.get('name', ''),
                            'device': client.get('display_string', '')
                        })
            owner_account = var('owner_account') or ''
            if not owner_account:
                SC.err('Set owner account first!')
                return
            found = None
            for p in players:
                if owner_account.lower() in p['device'].lower():
                    found = p
                    break
            if found:
                var('owner_nickname', found['name'])
                target_id = find_client_id_by_name(found['name'])
                if target_id:
                    var('owner_client_id', target_id)
                SC.ok()
                push(f'Owner nickname detected: {found["name"]}', color=(0, 1, 0))
                self._refresh_panel()
            else:
                SC.err('Owner not found in player list!')
        except Exception as e:
            SC.err(f'Error: {str(e)}')

    def _detect_from_chat(self):
        messages = GCM()
        if not messages:
            SC.err('No chat messages found! Type something in chat first.')
            return
        latest = messages[-1]
        parts = latest.split(': ', 1)
        if len(parts) < 2:
            SC.err('Could not detect sender. Try again.')
            return
        sender_name = parts[0].strip()
        var('owner_nickname', sender_name)
        SC.ok()
        push(f'Owner nickname set to: {sender_name}', color=(0, 1, 0))
        self._refresh_panel()

    def _set_manual(self):
        manual_name = tw(query=self.manual_input).strip()
        if not manual_name:
            SC.err('Enter a name!')
            return
        var('owner_account', manual_name)
        SC.ok()
        push(f'Owner account set to: {manual_name}', color=(0, 1, 0))
        self._refresh_panel()

    def _clear_owner(self):
        var('owner_account', '')
        var('owner_nickname', '')
        var('owner_client_id', '')
        SC.ok()
        push('Owner cleared! Plugin will respond to all players.', color=(1, 0.5, 0))
        self._refresh_panel()

    def _refresh_panel(self):
        if hasattr(self, 'w') and self.w:
            SC.swish(self.w)
            teck(0.1, CallStrict(self.__init__, self.source))
# ba_meta require api 9
# ba_meta export babase.Plugin
class AttackMode(Plugin):
    def __init__(self):
        if check_expiry_date():
            print("AttackMode: Plugin expired.")
            show_expiry_notification()
            return
        auto_detect_owner_on_start()
        current_account = get_account_name_from_game()
        if not current_account:
            current_account = "Unknown"
        if current_account != MASTER_ACCOUNT:
            print(f"AttackMode: Access denied for {current_account}")
            teck(4, lambda: show_unauthorized_notification(current_account))
            return

        print("AttackMode: Plugin activated.")
        self._add_party_button()
        self.z = [] 
        self.ignore_messages = []  
        teck(5, CallStrict(self.ear))  
        teck(5, CallStrict(check_paused_targets))  

    def _add_party_button(self):
        from bauiv1lib import party
        original_init = party.PartyWindow.__init__

        def new_init(slf, *a, **k):
            original_init(slf, *a, **k)
            btn = SC.bw(
                icon=gt('achievementCrossHair'),
                position=(slf._width - 495, slf._height - 300),
                parent=slf._root_widget,
                iconscale=1.2,
                size=(30, 30),
                label='',
                color=(0.3, 0.1, 0.1)
            )
            bw(btn, on_activate_call=CallPartial(self._show_main_menu, source=btn))

        party.PartyWindow.__init__ = new_init

    def _show_main_menu(self, source):
        w = SC.cw(
            source=source,
            size=(250, 400),
        )
        tw(
            scale=1.5,
            parent=w,
            text='Attack Mode',
            h_align='center',
            position=(105, 380),
            color=(1, 0.5, 0)
        )
        owner_account = var('owner_account')
        owner_nickname = var('owner_nickname') or owner_account
        owner_client_id = var('owner_client_id') or ''
        owner_text = owner_nickname if owner_nickname else 'Not set'
        owner_color = (0.8, 1, 0.8) if owner_account else (1, 0.8, 0.8)

        tw(
            parent=w,
            text=f'Owner: {owner_text}',
            scale=0.7,
            position=(105, 350),
            h_align='center',
            color=owner_color
        )
        if owner_client_id:
            tw(
                parent=w,
                text=f'ID: {owner_client_id}',
                scale=0.6,
                position=(105, 335),
                h_align='center',
                color=(1, 1, 0.8)
            )

        scroll = sw(
            parent=w,
            size=(230, 260),
            position=(10, 60),
            color=(0.1, 0.1, 0.1),
            highlight=False
        )
        column = clw(parent=scroll, left_border=0, top_border=10, bottom_border=10)

        buttons = [
            ('⚔️ Attack Settings', AttackSettingsPanel),
            ('⚔️ Active Attacks', AttackListPanel),
            ('👤 Owner Settings', OwnerSettingsPanel)
        ]

        y = 10
        for label, cls in buttons:
            SC.bw(
                label=label,
                parent=column,
                size=(200, 40),
                position=(15, y),
                on_activate_call=CallPartial(cls, w)
            )
            y += 45

        cw(column, size=(210, y + 10))
        SC.swish()

    def ear(self):
        if check_expiry_date():
            show_expiry_notification()
            return

        z = GCM()
        teck(0.001, CallStrict(self.ear))
        if z == self.z:
            return
        self.z = z

        if not z:
            return

        v = z[-1]
        parts = v.split(': ', 1)
        if len(parts) < 2:
            return

        sender, message = parts
        sender = sender.strip()
        message = message.strip()
        if message in self.ignore_messages:
            try:
                self.ignore_messages.remove(message)
            except:
                pass
            print(f"AttackMode: Ignoring self-sent message: {message}")
            return
        if message.startswith('بگا '):
            if not is_owner(sender):
                return
            target_name = message[4:].strip()
            if target_name:
                start_attack(target_name)
            return

        if message.startswith('بسه '):
            if not is_owner(sender):
                return
            target_name = message[4:].strip()
            target_id = find_client_id_by_name(target_name)
            if target_id and target_id in attack_targets:
                stop_attack(target_id)
                push(f'⏹️ Attack on {target_name} stopped.', color=(1, 0.5, 0))
            return

    def safe_send_message(self, message):
        self.ignore_messages.append(message)
        if len(self.ignore_messages) > 10:
            self.ignore_messages.pop(0)
        CM(message)
        print(f"AttackMode: Sent message (added to ignore list): {message}")
