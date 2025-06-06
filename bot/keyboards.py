from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.texts import *

keyboards = {
              "settings_kb": [
                            [button_faq_threshold], 
                            [button_top_k],
                            [button_update],
                            [button_info]
                          ],
              }


def get_keyboard(name: str, back: bool = False):
    if name not in keyboards:
        raise ValueError(f"Invalid name of keybord: {name}")
    current_keybord = []
    for key in keyboards[name]:
        current_keybord.append(
            [
                InlineKeyboardButton(text=text_key, callback_data=f"{text_key}")
                for text_key in key
            ]
        )
    if back:
        back_text = button_back_text
        current_keybord.append(
            [InlineKeyboardButton(text=back_text, callback_data=f"{back_text}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=current_keybord)