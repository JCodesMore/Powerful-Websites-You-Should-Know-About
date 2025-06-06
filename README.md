# SetupSpawn Shorts Scraper 🎬

**Automatically extract website recommendations from SetupSpawn's YouTube Shorts**

This tool watches SetupSpawn's YouTube channel and automatically collects all the website recommendations mentioned in their short videos. Instead of manually watching hundreds of videos to find useful tools and websites, this scraper does the work for you and organizes everything into a searchable spreadsheet.

## What This Does 🤖

SetupSpawn creates tons of YouTube Shorts showcasing cool websites, tools, and resources for developers and creators. This scraper:

- **Finds new videos** automatically from the SetupSpawn Shorts channel
- **Listens to what's said** by transcribing the audio from each video
- **Looks at what's shown** by analyzing video frames to catch URLs displayed on screen
- **Extracts the good stuff** like website names, what they're used for, and detailed descriptions
- **Organizes everything** into a clean CSV file you can open in Excel, Google Sheets, or Notion

## What You Get 📊

The scraper creates a spreadsheet with columns for:

- **Video Title** - The name of the YouTube Short
- **Website/Tool** - The recommended website or tool name
- **Use** - What the tool is used for (in simple terms)
- **Details** - More detailed description of features and benefits
- **Video URL** - Link back to the original video
- **Published Date** - When the video was posted

## How It Works 🔧

The scraper runs through several steps automatically:

1. **Discovery** - Scans the SetupSpawn channel for new Shorts
2. **Transcription** - Converts video audio to text to understand what's being said
3. **Analysis** - Uses AI to identify website recommendations and extract key details
4. **Vision** - Looks at video frames to catch URLs shown on screen
5. **Export** - Saves everything to a CSV file you can use anywhere

## Getting Started 🚀

### What You Need

- A computer with Python installed
- API keys for:
  - OpenAI (for AI analysis)
  - AssemblyAI (for transcription)
- About 10-15 minutes for initial setup

### Quick Setup

1. **Download the project** to your computer
2. **Install requirements**: Open a command prompt and run:
   ```
   pip install -r requirements.txt
   ```
3. **Set up your API keys** in the `config.yaml` file
4. **Run the scraper**:
   ```
   python -m src.cli run
   ```

### Configuration

Edit the `config.yaml` file to customize:
- How many videos to process at once
- Which date to start from (default goes back to 2021)
- Export settings and file locations

## Usage Examples 💡

**Run everything from scratch:**
```
python -m src.cli run
```

**Skip certain steps if you've already done them:**
```
python -m src.cli run --skip discover,transcript
```

**Process only recent videos:**
```
python -m src.cli run --since 2024-01-01
```

**Check what's been processed:**
```
python -m src.cli status
```

**Export your data:**
```
python -m src.cli export
```

## Understanding the Output 📋

Your results will be saved in the `data/exports/` folder as CSV files. Each row represents one website recommendation from a SetupSpawn video. You can:

- **Open in Excel or Google Sheets** for easy browsing
- **Import into Notion** to build your personal tool database
- **Filter and search** to find specific types of tools
- **Share with friends** who are looking for the same resources

## Full List of Tips 📝

| # | Use Case / Description | Website / Tool | Source Video |
| :--- | :--- | :--- | :--- |
| 1 | Extract vocals and instruments from songs | [remusic.ai](http://remusic.ai/ai-vocal-remover) | [Remove vocals from any song](https://www.youtube.com/watch?v=s_bb4DwfgEY) |
| 2 | Infinite emails | setupspawn@outlook.com | [Did you know this trick?](https://www.youtube.com/watch?v=21s0b5Tcmn4) |
| 3 | Extract text from images or PDFs using Windows Snipping Tool's OCR feature | No website | [PC Tricks You Didn't Know](https://www.youtube.com/watch?v=BCHPbPN44a8) |
| 4 | Generates smart study guides and flashcards from uploaded class materials | [thea.study](http://thea.study) | [Don't tell your Teachers](https://www.youtube.com/watch?v=WM3raNv8GOA) |
| 5 | Interactive historical map showing world changes across eras | [part324.com](http://part324.com) | [Why didn't I have this in school?](https://www.youtube.com/watch?v=Maymu8pmS94) |
| 6 | Detect if a photo is AI-generated or a deepfake | [faceonlive.com](https://faceonlive.com) | [I got catfished](https://www.youtube.com/watch?v=b8eZXmjfpv0) |
| 7 | Generate customized workouts based on equipment and target muscles | [musclewiki.com](http://musclewiki.com) | [Impress Your Imaginary Friends](https://www.youtube.com/watch?v=dPpufmzDql4) |
| 8 | Explore global cities by driving through their streets virtually | secure boredom | [This Game Cured My Boredom](https://www.youtube.com/watch?v=uBE8hJ5k7bE) |
| 9 | Website mentioned: chatgpt.com/?model=gpt-4o | [chatgpt.com](http://chatgpt.com/?model=gpt-4o) | [Should we be worried?](https://www.youtube.com/watch?v=TSbGIQDfBbA) |
| 10 | Hear actors voices better | [netflix.com](http://netflix.com) | [Netflix Doesn't Tell You This](https://www.youtube.com/watch?v=T959v9bdLfQ) |
| 11 | Find and listen to radio stations worldwide via an interactive map | [radiocast.co](http://radiocast.co) | [Radio Stations From Every Country](https://www.youtube.com/watch?v=tAp8c6u-GZ4) |
| 12 | Borrow millions of books and ebooks for free online | [openlibrary.org](http://openlibrary.org) | [Free Books?](https://www.youtube.com/watch?v=awSA5Mf_E30) |
| 13 | Interactive historical map showing world changes over time | [timemap.org](http://timemap.org) | [Did you know this?](https://www.youtube.com/watch?v=fhehGr9Jtsk) |
| 14 | Virtually explore cities worldwide by walking, driving, or flying through them | [citywalki.com](http://citywalki.com) | [Powerful website you need to know](https://www.youtube.com/watch?v=octMkvibGZw) |
| 15 | Generate coloring book pages from text prompts or uploaded images | [colorifyai.art](http://colorifyai.art) | [I wasted too much time with this](https://www.youtube.com/watch?v=YPK17Xi-C-0) |
| 16 | Generate 3D CAD models from text descriptions | [zoo.dev](http://zoo.dev/text-to-cad) | [Is this the future?](https://www.youtube.com/watch?v=_Q6Fc_i6qjE) |
| 17 | Generate brain rot videos from PDFs or text for focused studying | [google.com](http://google.com/search?q=pdf+to+brain+rot) | [This will get you Straight A's](https://www.youtube.com/watch?v=9qWVZJmyfP0) |
| 18 | Find cheap alternatives to any item | [spoken.io](http://spoken.io) | [Don't Fall For This!](https://www.youtube.com/watch?v=tHiijRI_6E4) |
| 19 | Track status of Google search result removal requests | [google/resultsaboutyou](http://google/resultsaboutyou) | [Delete yourself from the Internet](https://www.youtube.com/watch?v=diqt7PBqWsc) |
| 20 | Create 3D models from text descriptions and edit them interactively | [backflip.ai](http://backflip.ai) | [What would you do with this?](https://www.youtube.com/watch?v=Dwg_cm56GpI) |
| 21 | Discover hidden Netflix categories using secret category codes | [netflix.com](http://netflix.com) | [Netflix Doesn't Want You To Know](https://www.youtube.com/watch?v=luQGaJwFliA) |
| 22 | Provides detailed career roadmaps for various IT professions | [alpharoadmap.com](http://alpharoadmap.com) | [Keep This A Secret](https://www.youtube.com/watch?v=W4jo3aXIHNM) |
| 23 | Generate AI images from reference image | [google.com](http://google.com/search?q=ominicontrol+space) | [Is This Getting Too Real?](https://www.youtube.com/watch?v=tOqf8WDBHuQ) |
| 24 | Online marketplace for buying products with potential Black Friday deals | [amazon.com](http://amazon.com) | [Don't Buy on Black Friday Before Knowing This!](https://www.youtube.com/watch?v=R88ypfpmtMc) |
| 25 | Edit and transform photos using AI-powered brush tools | [magic.chenjunfeng.xyz](http://magic.chenjunfeng.xyz) | [Use This Wisely](https://www.youtube.com/watch?v=-CrwkcKs_40) |
| 26 | Simplifies online recipes by removing clutter and providing adjustable servings | No website | [Why do websites do this?](https://www.youtube.com/watch?v=Q_Ek4rWXKyo) |
| 27 | Generate realistic AI videos from text prompts or uploaded images | [hailuoai.video](http://hailuoai.video) | [Should we be worried?](https://www.youtube.com/watch?v=FBRjNpJK-7g) |
| 28 | A website that finds social media information by uploading a person's photo | No website | [Should we be scared?](https://www.youtube.com/watch?v=ZZhL7IsdyFc) |
| 29 | Create your own fantasy maps | [dungeonscrawl.com](http://dungeonscrawl.com) | [Create your own fantasy world](https://www.youtube.com/watch?v=iv2hKf41J1I) |
| 30 | AI tool to generate highly realistic images from text prompts | [fal.ai](http://fal.ai) | [Should we be worried about this?](https://www.youtube.com/watch?v=qGBeFJFMsOg) |
| 31 | Read public domain books while practicing typing | [entertained.app](http://entertained.app) | [This Helped Me So Much!](https://www.youtube.com/watch?v=aJIpFTaLu0c) |
| 32 | Check if your personal information has been leaked on the Dark web | [google.com](http://google.com) | [Your Information On The Dark Web](https://www.youtube.com/watch?v=lz049zRFhw0) |
| 33 | Create face swap videos, GIFs, and photos easily online | [vidwud.com](http://vidwud.com) | [Trick Everyone You Know](https://www.youtube.com/watch?v=ktALNFcrKgg) |
| 34 | Transcribes speech from video by analyzing lip movements using AI | [readtheirlips.com](http://readtheirlips.com) | [No More Secrets With This](https://www.youtube.com/watch?v=NlmLVVpRFrI) |
| 35 | Find and buy outfits from TV shows and characters | [shopyourtv.com](http://shopyourtv.com) | [Rip My Bank Account](https://www.youtube.com/watch?v=tJOFBfoLanw) |
| 36 | Build a knowledge tree for any topic with subtopics and detailed info | [tree-of-knowledge.org](http://tree-of-knowledge.org) | [Don't Tell Your Teachers](https://www.youtube.com/watch?v=2LMHmrF5EC8) |
| 37 | Find information about your car | [startmycar.com](http://startmycar.com) | [I Wish I Knew About This Sooner](https://www.youtube.com/watch?v=ZBiqap-xVzc) |
| 38 | Create step-by-step guides with screenshots for tasks | [scribehow.com](http://scribehow.com) | [A Powerful Website You Need To Know!](https://www.youtube.com/watch?v=7ohof4HzpaE) |
| 39 | Access various applications and games from a single site | [emupedia.net](http://emupedia.net) | [No one Know About This](https://www.youtube.com/watch?v=bJTM7Cng-og) |
| 40 | Find to find and update all applications on your pc | No website | [This CMD Prompt Trick is Insane](https://www.youtube.com/watch?v=UyMNxDAiZDE) |
| 41 | Generate short videos from text prompts or uploaded images | [klingai.com](http://klingai.com) | [This is Scary!](https://www.youtube.com/watch?v=UFrLxN50dbQ) |
| 42 | Generate AI art on Fire TV using voice commands | No website | [I Was Today Years Old When I Learned](https://www.youtube.com/watch?v=Y9Wz426MDn0) |
| 43 | Interactive bookmarklet that lets you fly a ship and remove elements on any website for points | secure boredom | [Cure Your Boredom With This](https://www.youtube.com/watch?v=Nh9tf2glkYc) |
| 44 | Check amazon item price history | [keepa.com](http://keepa.com) | [Do This Before Buying On Amazon](https://www.youtube.com/watch?v=osBSvmM7-bs) |
| 45 | Create prank screens and fake app screenshots for fun | [geekprank.com](http://geekprank.com) | [Don't Tell Your Friends About This!](https://www.youtube.com/watch?v=itit7KQfKxo) |
| 46 | Provides a database of anime character mugshots | [websim.ai](http://websim.ai) | [Create a Game or Website In Seconds](https://www.youtube.com/watch?v=zw7PJ34sSPA) |
| 47 | Find the true size of different countries around the world | [thetruesize.com](http://thetruesize.com) | [We Have Been Lied To](https://www.youtube.com/watch?v=OrETtcuuMpE) |
| 48 | Pranks your friends by randomly replacing images in browser with Nicholas Cage | nCage+ chrome extension | [Don't Do This To Your Friends](https://www.youtube.com/watch?v=ZwCBYEtKU3A) |
| 49 | Create AI videos from text | [lumalabs.ai](http://lumalabs.ai/dream-machine) | [Should We Be Worried About This?](https://www.youtube.com/watch?v=PrpN7JIpYJI) |
| 50 | Free online Photoshop-like image editor | [photopea.com](http://photopea.com) | [Free Online Tools You Need To Know](https://www.youtube.com/watch?v=xOc_oX6a36w) |
| 51 | Find the best current deals on video games and compare prices | [gg.deals](http://gg.deals) | [Find The Best Video Game Deals](https://www.youtube.com/watch?v=ekyCz1Yrf-Y) |
| 52 | Create 3D depth maps and animations from images | [leiapix.com](http://leiapix.com) | [Turn Your Photos Into 3D Images](https://www.youtube.com/watch?v=SVFUz6RQclc) |
| 53 | Create realistic fake update screens for pranks | [whitescreen.online](http://whitescreen.online) | [Don't Tell My Boss ðŸ¤«](https://www.youtube.com/watch?v=CxiVL4qqkBw) |
| 54 | Identify a picture's location by uploading the image | [geospy.ai](http://geospy.ai) | [Find Someone's Location](https://www.youtube.com/watch?v=8D_g_o9byLQ) |
| 55 | Animate drawings by uploading and adjusting motion points | [sketch.metademolab.com](http://sketch.metademolab.com) | [Animate Your Terrible Drawings!](https://www.youtube.com/watch?v=lm5fwepJpbY) |
| 56 | Generate custom QR codes from URLs using AI-generated images | [google.com](http://google.com/search?q=hugging+face+qr+code+generator) | [I Guarantee You Didn't Know This!](https://www.youtube.com/watch?v=2qTIoRR854U) |
| 57 | Combine two emojis into one using Google's emoji mashup tool | [google.com](http://google.com) | [Google Secrets I Guarantee You Didn't Know!](https://www.youtube.com/watch?v=yuhUwdzjlNE) |
| 58 | Access unblocked games at school or work | [artclass.site](http://artclass.site) | [Play Unblocked Games at School or Work](https://www.youtube.com/watch?v=3gLwyqJgbes) |
| 59 | Flight simulator built into Google Earth Pro desktop application | [google earth](http://google.com/earth) | [This Cured My Boredom](https://www.youtube.com/watch?v=zHrT4X8FNhI) |
| 60 | Check if your computer is turned on | [ismycomputeron.com](http://ismycomputeron.com) | [The Most Useful Computer Trick Ever](https://www.youtube.com/watch?v=BVTJliBUS-Y) |
| 61 | Discover and experiment with various AI tools including image generation and logo integration | [huggingface.co](http://huggingface.co) | [The Most Useful Ai Tools](https://www.youtube.com/watch?v=yEBgiITK28k) |
| 62 | Find notable people from any place in the world on an interactive map | [tjukanovt.github.io](http://tjukanovt.github.io/notable-people) | [Find Celebrities Near You](https://www.youtube.com/watch?v=IzeiBb_9B9U) |
| 63 | Provides step-by-step car maintenance videos and parts info | [carcarekiosk.com](http://carcarekiosk.com) | [This Website Saved Me](https://www.youtube.com/watch?v=u9N5ObU45Bk) |
| 64 | Generate apps, games, and websites from hand-drawn sketches | [sketch2app.io](http://sketch2app.io) | [Create A Game or Website With a Drawing](https://www.youtube.com/watch?v=pEnJK_UKEcQ) |
| 65 | Create AI comics | [huggingface.co](http://huggingface.co/spaces/jbilcke-hf/ai-comic-factory) | [Create A Comic Based On Your Life!](https://www.youtube.com/watch?v=ySzjCbgbJek) |
| 66 | Report and request blurring of personal or inappropriate images in Street View | [google maps](http://maps.google.com) | [I Was Today Years Old When](https://www.youtube.com/watch?v=B4pIbpbFJwo) |
| 67 | Library of categorized video effects with examples and names | [eyecannndy.com](http://eyecannndy.com) | [How To Create The Best Videos](https://www.youtube.com/watch?v=Iz-5s36TmJg) |
| 68 | Provides concise recipes by removing extra website content | [cooked.wiki](http://cooked.wiki) | [I Hate When Websites Do This!](https://www.youtube.com/watch?v=aKYsGuSoSKE) |
| 69 | Listen to radio stations worldwide via an interactive map | [radio.garden](http://radio.garden) | [A Powerful Website I Guarantee You Didn't Know](https://www.youtube.com/watch?v=xBqPQ9Gn4y8) |
| 70 | Create fake text messages or social media posts for demonstration | [fakedetail.com](http://fakedetail.com) | [Why You Shouldn't Trust Screenshots...](https://www.youtube.com/watch?v=jm-d8WMWQvA) |
| 71 | Create videos using AI prompts and explore GPT-powered tools | [chat.openai.com](http://chat.openai.com) | [Create an Entire Video with ChatGPT? #invideoAiPartner](https://www.youtube.com/watch?v=JQjzhbyTBQE) |
| 72 | Preview and edit AI-generated videos with free and paid plans | [invideo.io](http://invideo.io) | [Create an Entire Video with ChatGPT? #invideoAiPartner](https://www.youtube.com/watch?v=JQjzhbyTBQE) |
| 73 | Analyze and filter out fake and unnatural Amazon product reviews | [fakespot.com](http://fakespot.com) | [Amazon Doesn't Tell You This!](https://www.youtube.com/watch?v=UWNOcFwrn1w) |
| 74 | Resume keyword scanner to match your resume with job descriptions | [jobscan.co](http://jobscan.co) | [This Is Why You Can't Find A Job](https://www.youtube.com/watch?v=2ax2jMzsIzM) |
| 75 | Use GPT-4 and generate AI images on your phone for free | copilot app | [ChatGPT on Your Phone?](https://www.youtube.com/watch?v=q9mgX-nYqFU) |
| 76 | Uncensor a screenshot | No website | [Don't Get Caught Doing This!](https://www.youtube.com/watch?v=ddA5O-pQQS0) |
| 77 | Play a challenging and infuriating password creation game | [neal.fun](http://neal.fun/password-game/) | [The Most Frustrating Game Ever](https://www.youtube.com/watch?v=lxJYBCaW97A) |
| 78 | Open up excel workbook when boss/coworker enters room | No website | [Will My Boss Get Mad at Me For This?](https://www.youtube.com/watch?v=l7z_O--N4VE) |
| 79 | Generate AI art illusions incorporating your logo | [krea.ai](http://krea.ai/fun/logos) | [How Does This Even Work!?](https://www.youtube.com/watch?v=IbfibAc9FDA) |
| 80 | App to customize foot pedals for computer shortcuts and automation | No website | [I Never Have To Work Again](https://www.youtube.com/watch?v=dPVCvNtXEbE) |
| 81 | Find price history of item to avoid Black Friday scams | [keepa.com](http://keepa.com) | [Why Black Friday Is A Scam](https://www.youtube.com/watch?v=CPrtb0SlNNU) |
| 82 | Website mentioned: deskspacing.com | [deskspacing.com](http://deskspacing.com) | [Create Your Own Office](https://www.youtube.com/watch?v=w9TbmvLB4uw) |
| 83 | Mouse that auto jitters to keep you active status | [amazon.com](http://amazon.com) | [This Mouse Might Get Me In Trouble!](https://www.youtube.com/watch?v=w-dvHT7U8ik) |
| 84 | Fan summer/winter switch | No website | [Why Did No One Tell Me This?](https://www.youtube.com/watch?v=YY_cgJcZkwM) |
| 85 | Find appliance manuals, common problems, repair videos, and parts | [repairclinic.com](http://repairclinic.com) | [How Do I Fix This?](https://www.youtube.com/watch?v=bNrDq3zCZMY) |
| 86 | Website mentioned: outlook.com | [outlook.com](http://outlook.com) | [My Boss Fired Me](https://www.youtube.com/watch?v=VcDnjOxGFAM) |
| 87 | Check if your email has been involved in data breaches | [haveibeenpwned.com](http://haveibeenpwned.com) | [Someone Stole My Identity!](https://www.youtube.com/watch?v=wN4n-6QA45Y) |
| 88 | Free online versions of Word, Excel, PowerPoint, and Outlook | [microsoft365.com](http://microsoft365.com) | [Don't Buy That! Use This!](https://www.youtube.com/watch?v=cDau2VO83iY) |
| 89 | Windows network settings tool to view saved Wi-Fi passwords | No website | [Did you know about this PC Trick?](https://www.youtube.com/watch?v=5TXjZD6QYi4) |
| 90 | Fake wall charger hidden camera | No website | [Someone Was Spying On Me!](https://www.youtube.com/watch?v=yxZ46D7xTwk) |
| 91 | Permanantly delete browser data | No website | [Your Internet History Isn't Deleted!](https://www.youtube.com/watch?v=3scC9dza0Xc) |
| 92 | Turn rough sketches into realistic landscape images | [nvidia.com](http://nvidia.com/en-us/studio/canvas/) | [How I Became The Best Artist](https://www.youtube.com/watch?v=HFaXYQXKsKI) |
| 93 | Set gas prepaid amount without going inside | No website | [I Just Learned This Today](https://www.youtube.com/watch?v=XGoh89rhCdE) |
| 94 | Setup second desktop view | No tips found | [PC Shortcut Teacher's Don't Want You To Know!](https://www.youtube.com/watch?v=84JpK_Gfj9I) |
| 95 | Remove unwanted objects from photos by coloring over them | [photoeditor.ai](http://photoeditor.ai) | [Powerful Websites You Should Know!](https://www.youtube.com/watch?v=0jHctusPrj0) |
| 96 | Generate and modify images using AI based on uploaded pictures | [bing.com](http://bing.com/chat) | [Computer Trick I Guarantee You Didn't Know!](https://www.youtube.com/watch?v=AzHWPq-TFF8) |
| 97 | Access free AI courses to start learning and mastering AI skills | [cloudskillsboost.google](http://cloudskillsboost.google/journeys/118) | [Free Courses for AI](https://www.youtube.com/watch?v=3nS2JaAsMEI) |
| 98 | AI art generator that creates images from text prompts | [midjourney.com](http://midjourney.com) | [Create 3D Characters From Pictures](https://www.youtube.com/watch?v=oXhHWnO3wL8) |
| 99 | Play thousands of archived Flash games after Flash ended | [bluemaxima.org](http://bluemaxima.org/flashpoint/) | [Play Forgotten Flash Games](https://www.youtube.com/watch?v=5uDtPA7APwo) |
| 100 | Improve netflix audio | [netflix.com](http://netflix.com) | [Why Doesn't Netflix Tell You This?](https://www.youtube.com/watch?v=Iqnd16MPTH8) |
| 101 | Unfreeze your black screened PC | No website | [This Could Fix Your Computer!](https://www.youtube.com/watch?v=oOgTOFz5acE) |
| 102 | Find overstocked brand new items at discounted prices | [amazon.com](http://amazon.com) | [Online Shopping Secret](https://www.youtube.com/watch?v=7Ys8gu9Pny0) |
| 103 | AI tools for video style transfer and text-to-video generation | [app.runwayml.com](http://app.runwayml.com) | [The Future of Movies](https://www.youtube.com/watch?v=XqQwXlIPhsw) |
| 104 | Create AI-generated presentations quickly and easily | [gamma.app](http://gamma.app) | [I Shouldn't Show You This](https://www.youtube.com/watch?v=Qdh6bjACFZo) |
| 105 | Simulates mouse movement to keep your computer active | No website | [Will I Get Fired For This?](https://www.youtube.com/watch?v=-FlpIJqD8do) |
| 106 | Use loyalty number for reward at the pump | No website | [How to get Secret Rewards](https://www.youtube.com/watch?v=iJH9JOak8_o) |
| 107 | Free video editor | [vidmix.app](http://vidmix.app) | [I Found a Free Video Editor](https://www.youtube.com/watch?v=PtuP3-DS8KA) |
| 108 | Generates email templates based on user prompts within Gmail | [gmail.com](http://gmail.com) | [Will This Make Us Lazy?](https://www.youtube.com/watch?v=TT9DaBUZY3k) |
| 109 | Generate music tracks from text descriptions using AI | [aitestkitchen.withgoogle.com](http://aitestkitchen.withgoogle.com) | [Convert Text to a Song?](https://www.youtube.com/watch?v=eHJbu6xangc) |
| 110 | Play youtube video while iPhone locked | No website | [Don't Tell YouTube!](https://www.youtube.com/watch?v=u1KRfNsKoO8) |
| 111 | Download Nvidia app to keep eyes focused on camera during webcam use | [www.nvidia.com](http://www.nvidia.com) | [Genius or Creepy?](https://www.youtube.com/watch?v=4XIZ6KoRWr4) |
| 112 | Remote access PC from phone | [remotedesktop.google.com](http://remotedesktop.google.com) | [Control Your PC with a Phone?](https://www.youtube.com/watch?v=BO3dr0MAQpw) |
| 113 | Check recent activity and devices signed into your Google account | [myaccount.google.com](http://myaccount.google.com) | [Is Someone Spying on Your Google Account?](https://www.youtube.com/watch?v=hfQvaNDntoc) |
| 114 | Free video editing software with professional effects and tools | [blackmagicdesign.com](http://blackmagicdesign.com) | [Don't Buy Premiere Pro, Use This!](https://www.youtube.com/watch?v=1JpGnZH7PZg) |
| 115 | Launch asteroids anywhere on a map for interactive fun | [neal.fun](http://neal.fun/asteroid-launcher) | [Launch An Asteroid At Your City](https://www.youtube.com/watch?v=wVFJIsWFSig) |
| 116 | Generate customized cover letters from job descriptions | [chat.openai.com](https://chat.openai.com) | [Use ChatGPT To Get Any Job](https://www.youtube.com/watch?v=fNEQBFtkS-Y) |
| 117 | Check if your computer is currently on or off | [ismycomputeron.com](http://ismycomputeron.com) | [A Computer Tip You Need to Know!](https://www.youtube.com/watch?v=P1rCD_9H6DU) |
| 118 | Copy/paste in excel easily | No tips found | [Don't Make This Mistake in Excel](https://www.youtube.com/watch?v=1s_1_PMxkso) |
| 119 | Lock your car from farther away | No website | [Does This Car Trick Actually Work?](https://www.youtube.com/watch?v=XVI-e6AR5Gw) |
| 120 | Enhances PC productivity with window management and text extraction tools | [aka.ms](http://aka.ms/installpowertoys) | [Hidden Computer Tool You Need](https://www.youtube.com/watch?v=L6sOtXggGhA) |
| 121 | Simulates a fake OS update screen to hide procrastination | [fakeupdate.net](http://fakeupdate.net) | [Don't Tell your Boss the Computer Trick](https://www.youtube.com/watch?v=Sm8BYyNVoZY) |
| 122 | Remove water from iPhone speakers | [googleusercontent.com](youtube.com) | [Remember this Trick to Save Your Phone](https://www.youtube.com/watch?v=k_IMxkIklgo) |
| 123 | Enhances and improves voice recordings using AI | [podcast.adobe.com](http://podcast.adobe.com/enhance) | [Enhance Your Audio with This!](https://www.youtube.com/watch?v=yK-XZNQJpLQ) |
| 124 | Use your phone or tablet as a second touchscreen monitor for your PC | [spacedesk.net](http://spacedesk.net) | [Turn your Phone into a Monitor!](https://www.youtube.com/watch?v=jcH74QQ0Ccg) |
| 125 | Upload videos or GIFs to remove and change their backgrounds | [unscreen.com](http://unscreen.com) | [Remove the Background from a Gif](https://www.youtube.com/watch?v=KxuiJhPI8bE) |
| 126 | Access thousands of free courses from top universities like Harvard and MIT | [edx.org](http://edx.org) | [Find Free College Classes Online](https://www.youtube.com/watch?v=EQUJPYqMR5g) |
| 127 | Find part of a video faster by searching youtube transcript | [googleusercontent.com](youtube.com) | [YouTube Trick You Need To Know!](https://www.youtube.com/watch?v=2goGyaOz52g) |
| 128 | Use Windows Sandbox as airgapped second pc | No website | [PC Tip I Guarantee You Didn't Know!](https://www.youtube.com/watch?v=14P-OzCytaw) |
| 129 | Play a hidden text adventure game within Google's search page | [google.com](http://google.com) | [Google Has A Secret Game You Didn't Know!](https://www.youtube.com/watch?v=vgwn5uCyVdg) |
| 130 | Mute microwave keys | No website | [Did you know this Microwave Trick?](https://www.youtube.com/watch?v=iasx95s-gsk) |
| 131 | Microsoft Word's Editor tool for improving writing quality | No website | [Microsoft Word Trick Your Teachers Don't Tell You!](https://www.youtube.com/watch?v=0su4ElfuGnY) |
| 132 | Create godmode folder on your PC | No website | [Computer Trick I Guarantee You Didn't Know!](https://www.youtube.com/watch?v=H0MIlKL8Mzo) |
| 133 | Find hidden and unique places to visit in cities worldwide | [atlasobscura.com](http://atlasobscura.com) | [Secret Travel Spots No One Knows!](https://www.youtube.com/watch?v=oLsEhwmkH-8) |
| 134 | Search Gmail for emails with large attachments to free up space | [google.com](http://google.com/mail/u/4/#search/has%3Aattachment+larger%3A20MB) | [GMail Trick I Guarantee You Didn't Know!](https://www.youtube.com/watch?v=1PRAGGatMIs) |
| 135 | Generates a QR code for easy Wi-Fi access | unspecified website | [WiFi Trick I Guarantee You Didn't Know!](https://www.youtube.com/watch?v=apyiD1uh3xM) |
| 136 | Play a typing game to beat waves of falling words | [zty.pe](http://zty.pe) | [Become the Bestest Typer!](https://www.youtube.com/watch?v=lrrZf563FZw) |
| 137 | Create invisible folders on your desktop | No website | [Computer Trick I Guarantee You Didn't Know!](https://www.youtube.com/watch?v=k_x_Ooc27T0) |
| 138 | Reverse image search using facial recognition | [yandex.com](http://yandex.com/images/) | [Find Other Pictures of You on the Internet!](https://www.youtube.com/watch?v=ZYPwh1O_CQw) |
| 139 | Separates music and vocals from an uploaded MP3 track | [alphawaves.com](http://alphawaves.com) | [Separate Vocals and Instruments from Songs!](https://www.youtube.com/watch?v=AXcD4WOc2y8) |
| 140 | Read articles without logging in by accessing archived versions | [archive.is](http://archive.is) | [Did you know about this Internet trick?](https://www.youtube.com/watch?v=y1Bgktoxxq8) |
| 141 | Generate AI-written text like emails quickly | [beta.openai.com](http://beta.openai.com/playground/) | [This AI Will Write for You! ðŸ¤«](https://www.youtube.com/watch?v=LTdZKg5cxM4) |
| 142 | Records and documents step-by-step computer actions with screenshots | No website | [Computer Trick I Guarantee You Didn't Know!](https://www.youtube.com/watch?v=MLY4YEUu1tc) |
| 143 | Processing failed or no content found | No tips found | [Excel Tip I Guarantee You Didn't Know! ðŸ¤¯](https://www.youtube.com/watch?v=7XUFAy7OOQA) |
| 144 | Find free open source alternatives to paid software | [www.opensourcealternative.to](http://www.opensourcealternative.to) | [Top 3 Useful Websites You Should Know!](https://www.youtube.com/watch?v=GVhdPdtYwqM) |
| 145 | Find free Google Slides and PowerPoint templates | [slidesgo.com](http://slidesgo.com) | [Top 3 Useful Websites You Should Know!](https://www.youtube.com/watch?v=GVhdPdtYwqM) |
| 146 | Automatically remove watermarks from pictures | [watermarkremover.io](http://watermarkremover.io) | [Top 3 Useful Websites You Should Know!](https://www.youtube.com/watch?v=GVhdPdtYwqM) |
| 147 | Automatically moves your mouse to simulate activity while working from home | No website | [Don't tell your Boss about this! ðŸ¤«](https://www.youtube.com/watch?v=vW_vPP4dDhM) |
| 148 | Search for specific file types directly using file extension filters | [google.com](http://google.com) | [This Google Search Trick is a Lifesaver!](https://www.youtube.com/watch?v=NdD4G8yyS3g) |
| 149 | View all emails with 'unsubscribe' to manage subscriptions | [mail.google.com](http://mail.google.com/mail/u/1/#search/unsubscribe) | [Finally Stop Spam Emails with this Gmail Trick!](https://www.youtube.com/watch?v=7hYAHIeiJKc) |
| 150 | Excel's camera tool captures and links live snapshots of cell ranges. | No website | [Excel has been hiding this feature from you! ðŸ“·](https://www.youtube.com/watch?v=0gIdPcaVcO0) |
| 151 | Search school textbooks for step-by-step problem solutions | [litsolutions.org](http://litsolutions.org) | [Find the Answers to Any Textbook! ðŸ“š](https://www.youtube.com/watch?v=ldPCRpVXq08) |
| 152 | Find suppliers for any company by searching their shipments | [importyeti.com](http://importyeti.com) | [Top 3 Websites You Didn't Know Existed!](https://www.youtube.com/watch?v=mH3Ih6FkRGg) |
| 153 | Offers many tools for handling various file types including PDFs | [tinywow.com](http://tinywow.com) | [Top 3 Websites You Didn't Know Existed!](https://www.youtube.com/watch?v=mH3Ih6FkRGg) |
| 154 | Transfer files up to 2 gigabytes easily | [wetransfer.com](http://wetransfer.com) | [Top 3 Websites You Didn't Know Existed!](https://www.youtube.com/watch?v=mH3Ih6FkRGg) |
| 155 | Access and manage your Gmail email account | [mail.google.com](http://mail.google.com) | [No one knows about this GMail Trick!](https://www.youtube.com/watch?v=jTxRCEpUgt0) |
| 156 | Find platforms to make money in various work categories | [sidehustlestack.co](http://sidehustlestack.co) | [Find your Next Side Hustle to Make Extra ðŸ’°](https://www.youtube.com/watch?v=-AQ_Qt4SJYc) |
| 157 | Play classic console games directly in your browser | [emulatorgames.online](http://emulatorgames.online) | [I Might go to Jail for Telling You This... ðŸŽ®](https://www.youtube.com/watch?v=pyfkdBLwtHc) |
| 158 | Skip youtube ads automatically | [sponsor.ajay.app](http://sponsor.ajay.app) | [Mr. Beast Hates Me For This... ðŸ˜¡](https://www.youtube.com/watch?v=WoDyNrMPaYU) |
| 159 | Animate drawings by uploading and applying animations | [sketch.metademolab.com](http://sketch.metademolab.com) | [You can Animate your Drawings!](https://www.youtube.com/watch?v=OXdTw3wrJ9c) |
| 160 | Play a game guessing which YouTube video got more views based on thumbnail and title | secure boredom | [Guess which Thumbnails got the Highest Views ðŸŽ® w Matty McTech](https://www.youtube.com/watch?v=XMSCgFiEvAQ) |
| 161 | Compare video game prices across stores to find the best deal | [isthereanydeal.com](http://isthereanydeal.com) | [Find Cheap Video Games by Doing This! ðŸŽ®](https://www.youtube.com/watch?v=hZhMIBAY5Ik) |
| 162 | Tap iphone to open camera | No website | [Apple Kept This a SecretðŸ“±...](https://www.youtube.com/watch?v=ra3RPGcs2dk) |
| 163 | Website to 'download' additional RAM to speed up your computer | [downloadmoreram.com](http://downloadmoreram.com) | [Easily speed up your PC with this trick! ðŸ¤¯ w Matty McTech - #shorts](https://www.youtube.com/watch?v=y0f0ZI6UfDI) |
| 164 | Online photo editor for basic image editing as an alternative to Photoshop | [photopea.com](http://photopea.com) | [Don't Buy Photoshop! Use this Instead. ðŸ˜Š #shorts #photoshop #photoediting](https://www.youtube.com/watch?v=Zh-enGJGUmY) |
| 165 | Create AI-generated artwork from text prompts | [app.wombo.art](http://app.wombo.art) | [Create your own AI Generated NFT with this website](https://www.youtube.com/watch?v=Nu9wH96VZpE) |
| 166 | Default windows screensaver is an actual window | No website | [I bet you didn't know this! #windows #microsoft #windows 10](https://www.youtube.com/watch?v=YQifaR1ZXOY) |
| 167 | Find password of the wifi you are connected to | No website | [Find your WiFi password with ease](https://www.youtube.com/watch?v=iffjBXPX9Fo) |
| 168 | Generate and edit random maps for DND or role-playing games | [azgaar.github.io](http://azgaar.github.io) | [Create your own Fantasy World](https://www.youtube.com/watch?v=7oDVhVvRSPs) |
| 169 | Use emojis in windows | No website | [Secret Keyboard on your Computer](https://www.youtube.com/watch?v=CGMbj_JvW7k) |
| 170 | Generate speech using celebrity voices | [fakeyou.com](http://fakeyou.com) | [Pretend like you are a Celebrity](https://www.youtube.com/watch?v=i96Jr4ofG84) |
| 171 | Plug in a USB | No tips found | [That feeling when the USB finally goes in...](https://www.youtube.com/watch?v=xDNmbyJ2VYs) |
| 172 | Passwords that got celebs hacked | No tips found | [These Passwords got Celebrities Hacked](https://www.youtube.com/watch?v=T9mpjbE16ic) |
| 173 | Detect if a picture is photoshopped by analyzing image inconsistencies | [fotoforensics.com](http://fotoforensics.com) | [Expose Photoshopped Pictures?](https://www.youtube.com/watch?v=8AWvLUqUAYA) |
| 174 | Copy/paste multiple things in one go | No website | [You have been Copy Pasting Wrong](https://www.youtube.com/watch?v=nPZQhF6rMfI) |
| 175 | Watch youtube videos while doing other things | [googleusercontent.com](youtube.com) | [You have been Watching YouTube Wrong!](https://www.youtube.com/watch?v=4UfrfkSFlCA) |
| 176 | Create simple drawings and have AI transform them into realistic images | [nvidia-research-mingyuliu.com](http://nvidia-research-mingyuliu.com/gaugan/) | [This Website Will Cure your Boredom!](https://www.youtube.com/watch?v=mR3zm6wPMJg) |
| 177 | Find secret category codes to discover specific genres and content | [netflix-codes.com](http://netflix-codes.com) | [Netflix Secret Hidden Feature?](https://www.youtube.com/watch?v=8sOSUtp7dI8) |
| 178 | Find public Wi-Fi locations and passwords in your city | [wifimap.io](http://wifimap.io) | [Powerful Website you Should Know!](https://www.youtube.com/watch?v=OFUszRLmrsc) |
| 179 | Visualize the true size of countries or states compared to others | [thetruesize.com](http://thetruesize.com) | [You Have Been Lied to!](https://www.youtube.com/watch?v=g_wZ1C-Yu4E) |
| 180 | Programming expectation vs reality | No website | [Programming: Expectation vs Reality](https://www.youtube.com/watch?v=jNWpWsFERNM) |
| 181 | Unfreeze your black screened PC | No website | [A PC Tip I Guarantee You Didn't Know...](https://www.youtube.com/watch?v=DVJDUAgPKR4) |
| 182 | Find secret menu items for various restaurants | [hackthemenu.com](http://hackthemenu.com) | [I Found Secret Menu's for Fast Food Restaurants #shorts](https://www.youtube.com/watch?v=vXKLVKR_Js8) |
| 183 | Find password of the wifi you are connected to | No website | [Tell Me Your a Hacker Without Telling Me... #shorts](https://www.youtube.com/watch?v=6GPhFPvWjqs) |
| 184 | Provides workouts based on body weight and target muscle | [musclewiki.com](http://musclewiki.com) | [A Powerful Website you should know! #shorts](https://www.youtube.com/watch?v=0VVvGjybvRo) |





## Troubleshooting 🔧

**"Config file not found"** - Make sure `config.yaml` is in the same folder as the script

**"API key error"** - Check that your OpenAI and AssemblyAI keys are correctly set in the config file

**"No videos found"** - The scraper might have already processed all available videos, or there could be a connection issue

**Need help?** Check the log files in `data/exports/scraper.log` for detailed error messages.

## What Makes This Special ✨

- **Fully automated** - Set it up once and let it run
- **Smart extraction** - Uses both audio and visual analysis to catch everything
- **Handles failures gracefully** - If something goes wrong, it picks up where it left off
- **Export anywhere** - Works with all popular spreadsheet and database tools
- **Keeps learning** - Continuously improves at identifying website recommendations

## Technical Notes 🔍

This project uses modern AI and automation techniques:
- **YouTube API** for video discovery
- **AssemblyAI** for high-quality transcription
- **OpenAI GPT-4** for intelligent content analysis
- **Computer vision** for extracting URLs from video frames
- **SQLite database** for reliable data storage

Built with Python and designed to be maintainable, scalable, and easy to extend to other YouTube channels.

---

*This tool is designed to help developers and creators discover useful resources more efficiently. All data comes from publicly available YouTube content.*