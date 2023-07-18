import plugins.revLibs.pkg.process.revss as revss
import plugins.revLibs.pkg.process.impls.v1impl as v1impl
import plugins.revLibs.pkg.process.impls.edgegpt as edgegpt


def process_command(session_name: str, **kwargs) -> str:
    """处理命令"""

    cmd = kwargs['command']
    params = kwargs['params']

    reply_message = ""

    if cmd == 'reset':
        session: revss.RevSession = revss.get_session(session_name, kwargs["who"])
        if len(params) >= 1:
            prompt_whole_name = session.reset(params[0])
            reply_message = "已重置会话，使用情景预设: {}".format(prompt_whole_name)
        else:
            session.reset()
            reply_message = "已重置会话"
    elif cmd == "style":
        if kwargs["who"] == "newbing":
            import revcfg
            from EdgeGPT.conversation_style import ConversationStyle
            if len(params) >= 1:

                mapping = {
                    "创意": ConversationStyle.creative,
                    "平衡": ConversationStyle.balanced,
                    "精确": ConversationStyle.precise,
                }

                if params[0] not in mapping:
                    reply_message = "风格参数错误，可选参数: 创意, 平衡, 精确"
                    return reply_message

                setattr(revcfg, "new_bing_style", mapping[params[0]])

                reply_message = "已切换到{}风格，重置会话后生效".format(params[0])
            else:
                current = "创意"
                if getattr(revcfg, "new_bing_style") == ConversationStyle.balanced:
                    current = "平衡"
                elif getattr(revcfg, "new_bing_style") == ConversationStyle.precise:
                    current = "精确"
                reply_message = "当前风格为: {}，可选参数: 创意, 平衡, 精确\n例如: !style 创意".format(current)
        else:
            reply_message = "仅当使用New Bing逆向库时可切换风格"

    return reply_message
