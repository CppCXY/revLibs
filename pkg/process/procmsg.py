import time
import plugins.revLibs.pkg.process.revss as revss
from pkg.plugin.host import PluginHost
import logging
from mirai import MessageChain
from mirai.models.message import Forward,ForwardMessageNode
import traceback

def process_message(session_name: str, prompt: str, host: PluginHost, **kwargs) -> str:
    """处理消息"""
    session: revss.RevSession = revss.get_session(session_name)

    import revcfg

    # 重试循环
    fail_times = 0
    reply_message = ""
    while True:
        try:
            # 使用迭代器
            if revcfg.blog_msg_strategy == "send_section":
                for section in session.get_reply(prompt):
                    logging.info("分节回复: {}".format(section[:min(50, len(section))]))
                    if kwargs['launcher_type'] == 'group':
                        host.send_group_message(kwargs['launcher_id'], section)
                    elif kwargs['launcher_type'] == 'person':
                        host.send_person_message(kwargs['launcher_id'], section)

                reply_message = "<已发送完毕>"
            elif revcfg.blog_msg_strategy == "forward_msg_component":
                all_reply = ""

                use_forward_msg_component = False
                for section in session.get_reply(prompt):
                    if all_reply != "":
                        use_forward_msg_component = True
                    all_reply += section

                if use_forward_msg_component:
                    import config

                    bot_uin = config.mirai_http_api_config['qq']

                    forward_msg_node = ForwardMessageNode(
                        sender_id=bot_uin,
                        sender_name="revLibs",
                        message_chain=MessageChain([all_reply])
                    )

                    message_chain = Forward(nodeList=[forward_msg_node])

                    if kwargs['launcher_type'] == 'group':
                        host.send_group_message(kwargs['launcher_id'], message_chain)
                    elif kwargs['launcher_type'] == 'person':
                        host.send_person_message(kwargs['launcher_id'], message_chain)
                else:
                    reply_message = all_reply

            break
        except Exception as e:
            traceback.print_exc()
            if fail_times < revcfg.retry_when_fail:
                fail_times += 1
                logging.warn("失败，重试({}/{})...".format(fail_times, revcfg.retry_when_fail))
                time.sleep(2)
                continue
            else:
                raise e

    return reply_message