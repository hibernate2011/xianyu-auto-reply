"""渲染商品监控通知，复用公共渠道分发并记录邮件发送结果。"""
from __future__ import annotations

from typing import Any

from loguru import logger

from common.models.notification_channel import NotificationChannel
from common.services.email_log_service import (
    EMAIL_OPERATION_MONITOR_AI_NOTIFICATION,
    EMAIL_OPERATION_MONITOR_NOTIFICATION,
    record_email_log,
)
from common.services.notification_types import MONITOR_AI_NOTIFICATION_TYPE, resolve_stored_notification_types
from common.utils.notification_config import parse_notification_config
from common.utils.notification_dispatch import dispatch_notification
from common.utils.notification_template import render_notification_template


async def send_channel_message(
    channel: NotificationChannel,
    message: str,
    *,
    owner_id: int | None = None,
) -> bool:
    """兼容旧调用方，并委托公共通知分发器发送。

    Args:
        channel: 待发送消息的通知渠道。
        message: 通知正文。
        owner_id: 触发发送的用户ID。
    Returns:
        渠道发送成功返回True，否则返回False。
    """
    channel_type = str(channel.channel_type or "").strip().lower()
    try:
        config = parse_notification_config(channel.config_payload)
        return await dispatch_notification(
            channel_type,
            config,
            message,
            owner_id=owner_id,
        )
    except Exception:
        logger.exception("通知渠道发送异常：channel_id={}, owner_id={}", channel.id, owner_id)
        return False


async def send_monitor_item_notification(
    channel: NotificationChannel,
    context: dict[str, Any],
    *,
    owner_id: int | None = None,
) -> bool:
    """发送一条首次采集商品通知。"""
    default_message = (
        "【闲鱼商品监控】\n"
        f"任务: {context.get('task_name', '未知')}\n\n"
        f"商品: {context.get('title', '未知')}\n"
        f"价格: {context.get('price', '未知')}\n"
        f"地区: {context.get('area', '未知')}\n"
        f"卖家: {context.get('seller_nick', '未知')}\n"
        f"卖家信用: {context.get('seller_credit', '未知')}\n"
        f"包邮: {context.get('free_shipping', '未知')}\n"
        f"标签: {context.get('tags', '未知')}\n"
        f"链接: {context.get('item_url', '')}\n"
        f"时间: {context.get('time', '')}"
    )
    return await _send_monitor_notification(channel, "monitor", context, default_message, owner_id)


async def send_monitor_ai_notification(
    channel: NotificationChannel,
    context: dict[str, Any],
    *,
    owner_id: int | None = None,
) -> bool:
    """每个通知渠道发送该轮通过 AI 和阈值筛选的商品清单。"""
    default_message = (
        "【AI 商品购买推荐】\n"
        f"任务: {context['task_name']}\n"
        f"推荐商品: {context['item_count']} 件\n\n"
        f"{context['items']}\n\n"
        f"时间: {context['time']}"
    )
    return await _send_monitor_notification(
        channel, MONITOR_AI_NOTIFICATION_TYPE, context, default_message, owner_id
    )


async def _send_monitor_notification(
    channel: NotificationChannel,
    event_type: str,
    context: dict[str, Any],
    default_message: str,
    owner_id: int | None,
) -> bool:
    channel_type = str(channel.channel_type or "").strip().lower()
    trigger_operation = (
        EMAIL_OPERATION_MONITOR_AI_NOTIFICATION
        if event_type == MONITOR_AI_NOTIFICATION_TYPE
        else EMAIL_OPERATION_MONITOR_NOTIFICATION
    )
    try:
        config = parse_notification_config(channel.config_payload)
    except ValueError as exc:
        logger.exception("商品监控通知渠道配置无效：channel_id={}, owner_id={}", channel.id, owner_id)
        if channel_type == "email":
            await record_email_log(
                recipient_email="",
                trigger_operation=trigger_operation,
                success=False,
                owner_id=owner_id,
                result_message=str(exc),
            )
        return False
    notify_types, fallback = resolve_stored_notification_types(config.get("notify_types"))
    if fallback:
        logger.warning(
            "渠道 {}({}) 的通知类型配置异常，已按默认类型兼容",
            channel.name,
            channel.id,
        )
    if event_type not in notify_types:
        return False

    message = render_notification_template(config, event_type, context, default_message)
    try:
        return await dispatch_notification(
            channel_type,
            config,
            message,
            owner_id=owner_id,
            trigger_operation=trigger_operation,
        )
    except Exception as exc:
        logger.exception("商品监控通知发送异常：channel_id={}, owner_id={}", channel.id, owner_id)
        if channel_type == "email":
            await record_email_log(
                recipient_email=str(config.get("recipient_email") or ""),
                trigger_operation=trigger_operation,
                success=False,
                owner_id=owner_id,
                result_message=str(exc),
            )
        return False


__all__ = ["send_channel_message", "send_monitor_ai_notification", "send_monitor_item_notification"]
