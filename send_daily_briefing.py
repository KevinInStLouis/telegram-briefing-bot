def send_daily_briefing(chat_id: str | None = None,
                        when: datetime | None = None) -> str:
    """
    Python equivalent of sendDailyBriefing.

    - Pick chat_id from arg or TELEGRAM_CHAT_ID
    - Choose 'today' in America/Chicago (or New_York)
    - Fetch relevant memories
    - Build prompt, call LLM
    - Send via Telegram
    """
    if chat_id is None:
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not chat_id:
        raise RuntimeError("No chat ID provided or TELEGRAM_CHAT_ID missing")

    tz = ZoneInfo("America/Chicago")
    if when is None:
        when = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. Get memories
    memories = get_relevant_memories(when.date())

    # 2. Build prompt & generate text
    prompt = build_brief_prompt(memories, when)
    content = generate_briefing_content(prompt)

    # 3. Send via Telegram
    send_telegram_message(chat_id, content)

    return "Daily briefing sent successfully."
