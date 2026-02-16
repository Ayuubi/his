from his.utils import get_discount_levels


def boot_session(bootinfo):
    bootinfo.discount_levels = get_discount_levels()

