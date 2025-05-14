## Production email plan
- Sender: no-reply@elitedatingsearch.com
- Service: Postmark (Transactional plan) – revisit if >10 k msg/month
- DNS:
  - SPF: include:spf.mtasv.net
  - DKIM selector: pm
  - DMARC: v=DMARC1; p=none; rua=mailto:dmarc@elitedatingsearch.com
- Update `settings.py` + env vars
- Test with https://www.mail-tester.com/