def find_invite_by_code(invite_list, code):
    return next((inv for inv in invite_list if inv.code == code), None)
