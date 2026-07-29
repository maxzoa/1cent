# PayAI Bazaar Full Index Report

> [!IMPORTANT]
> **ARCHIVE / HISTORICAL SNAPSHOT.** This file records state at its stated stage/date. It is not
> current operating guidance. See [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md) and
> [DOCS_INDEX.md](DOCS_INDEX.md).

## Outcome

**PASS**. Controlled sequential indexing completed on 2026-07-22 from
11:36:04 UTC through 11:41:12 UTC.

- Catalog resources: 32
- Initially present: 1 (`/v1/url/status`)
- Missing and settled: 31
- Total authorized/spent: 113000 atomic = 0.113000 USDC
- HTTP 200: 31/31
- DB verify/settlement success: 31/31
- Base receipt status=1 and exact USDC transfer: 31/31
- Same-payload/payment-ID idempotency: 31/31
- Extra settlements: 0
- Final exact PayAI Bazaar resources: 32/32

## Backup and gates

- Fresh PostgreSQL backup: `backups/onecent-20260722T111909Z.sql.gz`, mode 600
- Buyer gate: 188000 >= 113000 atomic
- PayAI: x402 v2, exact, Base Mainnet and Bazaar capability confirmed
- API, DB and bot: healthy
- Mainnet monitor: PASS
- Operational pause: off
- Network, facilitator, seller, prices, public runtime and availability: unchanged

## Settlements

Every row has HTTP=200, PAYMENT-RESPONSE=PASS, DB verify=success,
DB settlement=success, receipt=1, exact seller delta, idempotency=PASS and one
settlement attempt.

| Resource | Atomic | Payment ID | Transaction hash |
|---|---:|---|---|
| `/v1/site/feeds` | 3000 | `pay_34d38957114841828267265531128d4d` | `0xe7e4dd94596e7580cb6cb0549cc406e78a18eaa0c0c9838fad1d6511b70aef28` |
| `/v1/site/llms-txt` | 3000 | `pay_7da09f479f1b41b6ab3fae1515ac477d` | `0x4e1a4b54b2f1bb83cbf5cfdb7fa8f0b7bd46b5590cea361c53ca2d279bd789a3` |
| `/v1/site/openapi` | 4000 | `pay_ee85794e40644d4d941cec4ebaf0f024` | `0x6dc833728b1e4b4556e2c0bba5ddc2fff83713d1fa5ecc334b8af0e2c2f3e435` |
| `/v1/site/robots` | 3000 | `pay_5dbe353ab0b546aab7ae684d68eddcae` | `0x4ed3cc39bfe391bf75fa4021a0971ca7c79b3bfbecf88515cb333048584472df` |
| `/v1/site/security-txt` | 3000 | `pay_a31e71ba3b3844689ce8a5f3b1273785` | `0x00e5e790ef7772dfe0677eeb830cf1d2c85ffed285ac52f93a013362a5aee9bd` |
| `/v1/site/sitemaps` | 4000 | `pay_a56fa00f7eff46298b579294eae12ddb` | `0xb9c1ef9e4ddc9afb68c327ec4b0e96607716a237e2f782e2f1ea265dec6f300a` |
| `/v1/url/access-flags` | 3000 | `pay_70a7a545beba477f8e68775a73e63ae4` | `0x6fc7d205d9e0ad579c188dd11c44b60ad8a8c6221d221dfd533c35e6005a4286` |
| `/v1/url/canonical` | 2000 | `pay_ff975774558b4cadb87127844d83cf62` | `0x9c5f49ff9e965d21e5e2bb4d7fbc3b8a09c3d6ae711914d3d4aadd97c78f87ca` |
| `/v1/url/changed` | 3000 | `pay_49d6a61c0a8a40cf99545263deb5ce0e` | `0x2af81cb161c94a7f9464957cd85162ebff85d570fe23482fc8323c1d2d14959c` |
| `/v1/url/content-type` | 2000 | `pay_024c1b54f41e4543af7faeca83eb134f` | `0xe76fcea8974750420cf2ea99941eb475b107bb42234fb0be642f39f92c8b00c6` |
| `/v1/url/diff` | 5000 | `pay_7e3d5a96633b4c86a7151b122546521b` | `0xc58519a21c8415dc0285a8935d7381fdff12093f74be623e911c4d54fa18c35d` |
| `/v1/url/extract` | 10000 | `pay_3744c050cdac4672905e35de7438ea3f` | `0x94f1079698f280017b926e51bbdafe11ab4036f151c02a763e2e88b9ca5842f2` |
| `/v1/url/hash` | 2000 | `pay_a5c2af32fa5b4db2a6d8c187668b95c4` | `0xc32bfb047d126d6a926f9c18ee78db7eeaa792ad28250db239c296a80e15ac64` |
| `/v1/url/headers` | 2000 | `pay_88b85c9a58d84344bb2727b10e56d6f1` | `0x03af94d22b86a9ff05ae1789a0abaf6ed639a1d55f75b38d025145e594c192a7` |
| `/v1/url/headings` | 3000 | `pay_c96afc6d1a1c4a24914b7581c9294a54` | `0xb5b4674364a265a07c16d8068d9fe7018f61466a8474cc6dc00e8949439e1e7a` |
| `/v1/url/images` | 4000 | `pay_276335bb34c74103b2ae157f3a1469a2` | `0x784f2c300cee7c644bc8670ca01290c78bb0f818bda7bb2dbba8da3a809ee2ab` |
| `/v1/url/jsonld` | 3000 | `pay_047fdedfb25348a1a685a091469fa898` | `0xd75e92699e7424842587c2c0c1117a33fd2c4a23caac4c02281a6b0c340eecad` |
| `/v1/url/language` | 2000 | `pay_fb9ea1d3a8144c958764d5ed7c1765ab` | `0xe75f168c179628973899e53c739cc78d8da452efc89077a0f8359fa333992819` |
| `/v1/url/links` | 4000 | `pay_2d078198f3014feb9006bbaedf823c2c` | `0xbee55657652cd04941ab870a713a94da318d7f19a6f54386e731a29104322039` |
| `/v1/url/markdown` | 5000 | `pay_3bdfc50a41604813812c9a3052612a7a` | `0x252c99d459bab2462c275dc483b3c4dda9126757b0112e6b25906e981b94c79b` |
| `/v1/url/metadata` | 3000 | `pay_f4a761ab73184f138ca9a3c44e8fdb7f` | `0x844adea45e98251524961a4020dbc5490d00781f8c603f6f9354224fdf0783fb` |
| `/v1/url/passport` | 10000 | `pay_017468272e7c45a9985dc08edf30d842` | `0x9e881e0bec4de304f36f7789ddc040198a4929ddf0d170542a8dfce4bd3e90cc` |
| `/v1/url/pulse` | 3000 | `pay_8962cb56295a45cdb1e0b62f7d9f1186` | `0xd110977e68738bd3cd3560c684348a213cc93b1a63e27eda70dcc54437a0d61e` |
| `/v1/url/rag-chunks` | 7000 | `pay_7397803f70c34196a26ba537228e166d` | `0xcb07fd4d1fc8495c2817679daa66b403a9816cc2831f727223ff8c9fcd3f54fb` |
| `/v1/url/redirects` | 2000 | `pay_a969877290744948b674401fa1a293ad` | `0xcab4f87d0ad218686b21eb1473df455978b15e9a3067fcd9e388d5b9780500dc` |
| `/v1/url/security-headers` | 3000 | `pay_cc241ff0f50b48af94987bec4572d6a8` | `0x87c6548ec5d9dc11112ecc65b33ef724b29e70272e8c9b873a18945ac74a9b2f` |
| `/v1/url/social-cards` | 3000 | `pay_d21c41bcfdbf42509eb2c3adc86ecdce` | `0x404f5f576d00c0e19cdea6bd8826bbe9a7052e3477cffb22e9a3b46c572dcc0a` |
| `/v1/url/text` | 4000 | `pay_0385cd3b4fcc4217b7b24ce83d2c0ed8` | `0x0679be0da9660f5cb059b248a21c59fa20b59a2e627355729440d4777f3c71cf` |
| `/v1/url/timing` | 2000 | `pay_a23c10281ef442909aebdeb063a3d8e0` | `0x0bcb9155e2b99d482a34d011c795a1feb0e57ce74ae54789aa076f2adc5c1812` |
| `/v1/url/tls` | 3000 | `pay_8e35655e179b4cafa97cfb5653076fef` | `0x6cadffc7c24d9865fcadcf8849eef1d103a1988160094291b234b525974637c3` |
| `/v1/url/word-stats` | 3000 | `pay_6a014178433d4de1b01d1b8f36bef8cd` | `0xe6e8aeae87f8a0612aef54f830c73a3b6a193fde560fcf925c76f69802d0eca0` |

`/v1/url/status` was rechecked, found in Bazaar, and skipped without payment.

## Bazaar final state

Read-only final discovery returned all 32 exact resource URLs. All 31 new
resources were already present on their immediate post-settlement checks; no
extra polling payment was made. Missing/unindexed resources: **none**.

## Balances and limits

- Buyer: 188000 -> 75000 atomic (delta -113000)
- Seller: 12000 -> 125000 atomic (delta +113000)
- Approved buyer floor: 75000 atomic; actual: 75000 atomic; PASS
- Temporary settlement limit: 10 -> 40 through SettingsService + audit
- `finally` restoration: 40 -> 10 through SettingsService + audit; verified
- Daily revenue limit: 1000000 atomic (1 USDC), unchanged

## Production final state

- Local and public `/health`: PASS, x402-v2-mainnet, service enabled
- Mainnet monitor: `mainnet_health=PASS`
- `onecent-api`, `onecent-bot`, `onecent-db`: healthy
- Containers were not recreated
- No network, facilitator, asset, seller, price or public deployment change
