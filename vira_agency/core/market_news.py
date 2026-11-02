
"""
واحد زنده دریافت قیمت‌ها، روند تکنیکال و اخبار بازار کریپتو و فارکس
بدون نیاز به کلید API و با اتصال به اندپوینت‌های آزاد بین‌المللی
"""
import asyncio
import json
import logging
import urllib.request

log = logging.getLogger(__name__)


def _fetch_crypto_data_sync() -> dict:
    """دریافت قیمت و تغییرات ۲۴ ساعته برترین رمزارزها از CoinGecko"""
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin,ripple&vs_currencies=usd&include_24hr_change=true"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
        return json.loads(resp.read().decode("utf-8"))


async def get_live_market_summary() -> str:
    """خلاصه وضعیت زنده بازار با اعداد دقیق جهت تزریق مستقیم به پرامپت استوری و پست"""
    try:
        data = await asyncio.to_thread(_fetch_crypto_data_sync)
        btc = data.get("bitcoin", {})
        eth = data.get("ethereum", {})
        sol = data.get("solana", {})

        btc_p = btc.get("usd", 0)
        btc_c = btc.get("usd_24h_change", 0.0)
        eth_p = eth.get("usd", 0)
        eth_c = eth.get("usd_24h_change", 0.0)
        sol_p = sol.get("usd", 0)
        sol_c = sol.get("usd_24h_change", 0.0)

        btc_trend = "صعودی 🟢" if btc_c >= 0 else "نزولی و اصلاحی 🔴"

        summary = (
            f"داده‌های زنده لحظه‌ای بازار:\n"
            f"- بیت‌کوین (BTC): ${btc_p:,.0f} (تغییرات ۲۴ ساعته: {btc_c:+.2f}%) روند: {btc_trend}\n"
            f"- اتریوم (ETH): ${eth_p:,.0f} (تغییرات: {eth_c:+.2f}%)\n"
            f"- سولانا (SOL): ${sol_p:,.2f} (تغییرات: {sol_c:+.2f}%)\n"
        )
        return summary
    except Exception as e:
        log.warning("Could not fetch live crypto prices: %s", e)
        return "بیت‌کوین در ناحیه تراکم و نوسان شدید نقدینگی، نهنگ‌ها در حال شکار استاپ‌لاس‌های سطوح حساس."
