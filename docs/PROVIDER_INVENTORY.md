# Provider Registry — AI Simplified Lab Video Factory

Audit date: 2026-11-06

## Factory rules
- Separate repository from YouTube Strategist.
- Prefer free, no-watermark and rights-clear workflows; free access is not automatically commercial permission.
- Cost preflight every generative action. Unknown cost means stop and ask.
- Keep provider-independent project/timeline data.
- Faceless channel; no identifiable real faces.
- Simple, language-neutral English narration for a predominantly Telugu-speaking audience.
- Select 9:16 Shorts or 16:9 horizontal per story.
- No automatic YouTube publishing or metadata changes.

## Provider snapshot
| Provider | Verified status | Best role | Limit / caution |
|---|---|---|---|
| Porter Metrics | Authenticated; no active subscription; no third-party integrations connected; quota unknown | Research, single scene clips, TTS, music, SFX, transcription | Never assume free. No confirmed multi-clip timeline editor/export. |
| PREVIS / Mad Genius AI | Connected; Candyland scene rendered previously; quota unknown | 3D previs, blockouts, camera paths | Numeric quota not exposed. |
| AI Producer by OpusClip | Temporary free access reported available | First assembly/export test | Free access is temporary; scene restyle 6 credits/sec, retry may double. |
| Pollo AI | Free plan; 8 credits | Selective image/video/audio generation | Low balance; quote before use. |
| Hansora AI | 15 credits; image models only within balance | Still assets/storyboards | Video not within current balance. |
| Higgsfield | Free plan; 0 credits; trial not started | Optional future generator | No current generation balance. |
| OpenArt | Free plan; 0 credits | Optional future generator | No current generation balance. |
| InVideo | 0 AI credits | Manual editing fallback | Manual no-watermark export documented; verify account. |
| Adobe | Connected; 96 MCP tools; plan unknown | Editing, quick cuts, audio enhancement, packaging | Tool access is not proof of free entitlement. |
| Canva | Connected; 43 MCP tools; entitlement unknown | Thumbnails, graphics, simple video | Check asset licence and watermark per element. |
| ElevenLabs | Connected; plan/balance not exposed | TTS, voice design, SFX, transcription, music | Free commercial-use restrictions; verify terms. |
| Descript | Connected; quota unknown | Transcript editing, captions, screen recording | Public Free export capped at 720p. |
| Kapwing | Free workspace: 10 credits; 10 transcription min; 10 translation min; 0.806 TTS min; 1 repurpose; 1 lip-sync min; 5GB storage; 30 min export | Caption/dub tests | Free exports watermarked. |
| OpusClip | API/MCP requires Pro, Max or Enterprise | Long-to-short repurposing | Not primary assembly on current plan. |
| Templated | 0/50 renders used | Repeatable graphics/end cards | Not a generative scene editor. |
| ImagineArt | Connected; org/balance unresolved | Optional image/video/music/speech | Balance unknown. |
| Clipwave | Connected; 4 tools; quota unknown | Media generation/project prep | Check cost in workspace. |
| Kittl | Connected; account lookup not completed | Design/mockups | Approval/login declined; don't retry without user initiation. |
| vidIQ | Free; 0/150 credits; reset 2026-11-08 08:03 UTC | Outlier/topic research | Save credits for high-value research. |
| ChannelzIQ | Solo plan; catalogue accessible; advanced Creator features blocked | Channel catalogue/transcripts/content gaps | Advanced analytics limited. |
| Windsor.ai | Trial; channel verified; 277 public videos | Private YouTube analytics | Trial, not confirmed free forever. |
| Ubersuggest | Free: 3 reports/day, 1 used; 1 project; 25 keywords; 2 competitors; 10 ideas | Search demand validation | Tight limits. |
| Ahrefs | Connected; prior query blocked by plan/API limit | Optional SEO validation | Not dependable currently. |
| GitHub | Connected | Factory source/version control | Existing ai_video_factory repository is the home. |
| Metricool | Connected; quota unknown | Scheduling/social analytics | Optional; publishing approval-gated. |
| Notion | Connected | Persistent inventory and SOP | Inventory page saved. |

## Porter creative studio
- Image profiles: image.text, image.text.pro, image.text.fast, image.edit, image.compose.
- Video profiles: video.text, video.image, video.premium, video.edit, video.interactive.
- Aspect ratios 9:16 and 16:9; allowed durations 4, 6 or 8 seconds; documented 720p/1080p.
- Video generation is async: creative.generate, then creative.get_result, then permanent asset_url.
- Generated clips include native audio; quoted dialogue can be spoken.
- video.edit modifies a single existing clip; this is not a multi-clip timeline.
- No 3D meshes, upscaling or lip-sync to supplied audio in the creative studio.

## Porter audio
- TTS: audio.text_to_speech and audio.text_to_speech_url.
- Voice search/preview: audio.search_voice_library, audio.search_voices, audio.text_to_voice, audio.get_voice, audio.create_voice_from_preview.
- Music: audio.compose_music and audio.video_to_music.
- SFX: audio.text_to_sound_effects and audio.sound_effects_url.
- Utilities: speech-to-text, speech-to-speech, isolate audio.
- Models include Eleven v4, v4 Turbo, v3 and v3 Conversational; Telugu is listed for v4/v4 Turbo and v3 Conversational.
- No cost/quota data returned: do not generate until a quote or explicit small-test approval.

## Porter research
- Perplexity search, ask and reason.
- Firecrawl browser, scrape, crawl, extract and autonomous research.
- YouTube SERP organic search, video metadata and subtitles/transcripts.

## Recommended provider roles
- Research: vidIQ, Windsor, ChannelzIQ, Ubersuggest, Porter search/Firecrawl/YouTube SERP and primary sources.
- Script: source-backed fact sheet, hook, story arc, scene plan and CTA.
- 3D scene planning: PREVIS.
- Generated clips: select provider by available balance and cost quote; Porter is a candidate, not assumed free.
- Voice/music/SFX: YouTube Audio Library for final monetized music unless another commercial licence is verified.
- Assembly: AI Producer first proof; InVideo manual fallback; Adobe if account entitlement confirmed.
- Deterministic fallback: existing FFmpeg/HyperFrames pipeline.
- Packaging: Canva, Adobe Express or Templated using only permitted free assets.

## Terms to recheck
- InVideo: https://help.invideo.io/en/articles/9380226-can-i-use-invideo-ai-for-free
- ElevenLabs: https://elevenlabs.io/pricing
- OpusClip: https://www.opus.pro/pricing
- Canva India: https://www.canva.com/en_in/pricing/
- Adobe Express: https://helpx.adobe.com/express/web/adobe-express-subscription/free.html
- Descript: https://www.descript.com/price
- Kapwing: https://www.kapwing.com/help/is-kapwing-free/
- Higgsfield: https://higgsfield.ai/pricing
- OpenArt: https://openart.ai/suite/pricing

Refresh public terms monthly and balances before every production.