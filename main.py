import traceback

from pkg.plugin.models import *
from pkg.plugin.host import EventContext, PluginHost

import time
import os

from revChatGPT.V1 import Chatbot

import plugins.revLibs.pkg.process.revss as revss
import plugins.revLibs.pkg.process.procmsg as procmsg
import plugins.revLibs.pkg.process.proccmd as proccmd
from EdgeGPT.conversation_style import ConversationStyle
"""
接入ChatGPT的逆向库
"""


def check_config():
    this_file = __file__

    template_file = os.path.join(os.path.dirname(this_file), "revcfg-template.py")

    # 检查revlib.py是否存在
    if not os.path.exists("revcfg.py"):
        # 不存在则使用本模块同目录的revcfg-template.py复制创建
        with open(template_file, "r", encoding="utf-8") as f:
            template = f.read()

        with open("revcfg.py", "w", encoding="utf-8") as f:
            f.write(template)

        return False

    return True


# 注册插件
@register(name="revLibs", description="接入acheong08/ChatGPT等逆向库", version="0.6.0", author="RockChinQ")
class RevLibsPlugin(Plugin):
    chatbot: Chatbot = None

    # 插件加载时触发
    def __init__(self, plugin_host: PluginHost):
        # 执行依赖库更新
        # try:
        #     import plugins.revLibs.pkg.utils as utils
        #     # utils.upgrade_revlibs()
        # except:
        #     traceback.print_exc()
        #     logging.warn("[rev] 依赖库更新失败，不能确保逆向库正常运行")

        if not check_config():
            logging.error("[rev] 已生成配置文件(revcfg.py)，请按照其中注释填写配置文件后重启程序")
            # plugin_host.notify_admin("[rev] 已生成配置文件(revcfg.py)，请按照其中注释填写配置文件后重启程序")
            return

        import revcfg

        if not hasattr(revcfg, "new_bing_style"):
            setattr(revcfg, "new_bing_style", ConversationStyle.balanced)

        import config

        revcfg.process_message_timeout = config.process_message_timeout
        config.process_message_timeout = 10 * 60
        logging.info("[rev] 已将主程序消息处理超时时间设置为10分钟")

        allow_role = {"newbing", "gpt4"}
        @on(PersonNormalMessageReceived)
        @on(GroupNormalMessageReceived)
        def normal_message_received(inst, event: EventContext, **kwargs):
            reply_message = ""
            try:
                if kwargs["who"] not in allow_role:
                    return

                reply_message = procmsg.process_message(
                    session_name=kwargs['launcher_type'] + "_" + str(kwargs['launcher_id']),
                    prompt=kwargs['text_message'], **kwargs)

                logging.debug("[rev] " + reply_message)

                reply_message = reply_message
            except Exception as e:
                logging.error("[rev] " + traceback.format_exc())
                import config
                if config.hide_exce_info_to_user:
                    reply_message = config.alter_tip_message
                    kwargs['host'].notify_admin("[rev] 处理消息时出现错误:\n" + traceback.format_exc())
                else:
                    reply_message = "处理消息时出现错误，请联系管理员" + "\n" + traceback.format_exc()

            if reply_message != "":
                event.add_return(
                    "reply",
                    ["{}\n\n[{}]".format(reply_message, kwargs["who"])]
                )

            event.prevent_default()
            event.prevent_postorder()

        @on(PersonCommandSent)
        @on(GroupCommandSent)
        def command_send(inst, event: EventContext, **kwargs):
            reply_message = ""
            try:
                if kwargs["who"] not in allow_role:
                    return

                reply_message = proccmd.process_command(
                    session_name=kwargs['launcher_type'] + "_" + str(kwargs['launcher_id']),
                    **kwargs)

                logging.debug("[rev] " + reply_message)
            except Exception as e:
                logging.error("[rev] " + traceback.format_exc())
                reply_message = "处理命令时出现错误，请联系管理员" + "\n" + traceback.format_exc()

            if reply_message.strip() != "":
                event.add_return(
                    "reply",
                    ["{}(cmd)".format(revcfg.reply_prefix) + reply_message],
                )
                event.prevent_default()
                event.prevent_postorder()

    def make_reply(self, prompt, **kwargs) -> dict:
        reply_gen = self.chatbot.ask(prompt, **kwargs)
        reply = {}

        for r in reply_gen:
            reply = r

        return reply

    # 插件卸载时触发
    def __del__(self):
        pass
