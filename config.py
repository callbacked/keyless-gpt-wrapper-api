MODEL_MAPPING = {
    "keyless-gpt-4o-mini": "gpt-4o-mini",
    "keyless-gpt-o3-mini": "o3-mini",
    "keyless-claude-3-haiku": "claude-3-haiku-20240307",
    "keyless-mixtral-8x7b": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "keyless-meta-Llama-3.3-70B-Instruct-Turbo": "meta-llama/Llama-3.3-70B-Instruct-Turbo"
}
VOICES = {
    # English Voices - Standard
    'en_uk_001': {'name': 'Narrator (Chris)', 'language': 'en-UK', 'category': 'standard'}, #works
    'en_uk_003': {'name': 'UK Male 2', 'language': 'en-UK', 'category': 'standard'}, # works 
    'en_female_emotional': {'name': 'Peaceful', 'language': 'en-US', 'category': 'standard'}, # works 
    'en_au_001': {'name': 'Metro (Eddie)', 'language': 'en-AU', 'category': 'standard'}, # works
    'en_au_002': {'name': 'Smooth (Alex)', 'language': 'en-AU', 'category': 'standard'}, # works
    'en_us_002': {'name': 'Jessie', 'language': 'en-US', 'category': 'standard'}, # works
    'en_us_006': {'name': 'Joey', 'language': 'en-US', 'category': 'standard'}, # works
    'en_us_007': {'name': 'Professor', 'language': 'en-US', 'category': 'standard'}, # works
    'en_us_009': {'name': 'Scientist', 'language': 'en-US', 'category': 'standard'}, # works
    'en_us_010': {'name': 'Confidence', 'language': 'en-US', 'category': 'standard'}, # works

    # English Voices - Character
    'en_female_samc': {'name': 'Empathetic', 'language': 'en-US', 'category': 'character'}, # works
    'en_male_cody': {'name': 'Serious', 'language': 'en-US', 'category': 'character'}, # works
    'en_male_narration': {'name': 'Story Teller', 'language': 'en-US', 'category': 'character'}, # works
    'en_male_funny': {'name': 'Wacky', 'language': 'en-US', 'category': 'character'}, # works
    'en_male_jarvis': {'name': 'Alfred', 'language': 'en-US', 'category': 'character'},  # works
    'en_male_santa_narration': {'name': 'Author', 'language': 'en-US', 'category': 'character'}, # works
    'en_female_betty': {'name': 'Bae', 'language': 'en-US', 'category': 'character'}, # works
    'en_female_makeup': {'name': 'Beauty Guru', 'language': 'en-US', 'category': 'character'}, # works
    'en_female_richgirl': {'name': 'Bestie', 'language': 'en-US', 'category': 'character'}, # works
    'en_male_cupid': {'name': 'Cupid', 'language': 'en-US', 'category': 'character'}, # works 
    'en_female_shenna': {'name': 'Debutante', 'language': 'en-US', 'category': 'character'}, # works
    'en_male_ghosthost': {'name': 'Ghost Host', 'language': 'en-US', 'category': 'character'}, # works
    'en_female_grandma': {'name': 'Grandma', 'language': 'en-US', 'category': 'character'}, # works
    'en_male_ukneighbor': {'name': 'Lord Cringe', 'language': 'en-US', 'category': 'character'}, # works
    'en_male_wizard': {'name': 'Magician', 'language': 'en-US', 'category': 'character'}, # works 
    'en_male_trevor': {'name': 'Marty', 'language': 'en-US', 'category': 'character'}, # works
    'en_male_deadpool': {'name': 'Mr. GoodGuy (Deadpool)', 'language': 'en-US', 'category': 'character'}, # works
    'en_male_ukbutler': {'name': 'Mr. Meticulous', 'language': 'en-US', 'category': 'character'}, # works
    'en_male_petercullen': {'name': 'Optimus Prime', 'language': 'en-US', 'category': 'character'}, # not working
    'en_male_pirate': {'name': 'Pirate', 'language': 'en-US', 'category': 'character'}, # works
    'en_male_santa': {'name': 'Santa', 'language': 'en-US', 'category': 'character'}, # works
    'en_male_santa_effect': {'name': 'Santa (w/ effect)', 'language': 'en-US', 'category': 'character'}, # works
    'en_female_pansino': {'name': 'Varsity', 'language': 'en-US', 'category': 'character'}, # works
    'en_male_grinch': {'name': 'Trickster (Grinch)', 'language': 'en-US', 'category': 'character'}, # works

    # English Voices - Disney
    'en_us_ghostface': {'name': 'Ghostface (Scream)', 'language': 'en-US', 'category': 'disney'}, # works
    'en_us_chewbacca': {'name': 'Chewbacca (Star Wars)', 'language': 'en-US', 'category': 'disney'}, # works
    'en_us_c3po': {'name': 'C-3PO (Star Wars)', 'language': 'en-US', 'category': 'disney'}, # works
    'en_us_stormtrooper': {'name': 'Stormtrooper (Star Wars)', 'language': 'en-US', 'category': 'disney'}, # works
    'en_us_stitch': {'name': 'Stitch (Lilo & Stitch)', 'language': 'en-US', 'category': 'disney'}, # works
    'en_us_rocket': {'name': 'Rocket (Guardians of the Galaxy)', 'language': 'en-US', 'category': 'disney'}, # works
    'en_female_madam_leota': {'name': 'Madame Leota (Haunted Mansion)', 'language': 'en-US', 'category': 'disney'}, # works

    # English Voices - Song
    'en_male_sing_deep_jingle': {'name': 'Song: Caroler', 'language': 'en-US', 'category': 'song'}, # works
    'en_male_m03_classical': {'name': 'Song: Classic Electric', 'language': 'en-US', 'category': 'song'}, # works
    'en_female_f08_salut_damour': {'name': 'Song: Cottagecore (Salut d\'Amour)', 'language': 'en-US', 'category': 'song'}, # works
    'en_male_m2_xhxs_m03_christmas': {'name': 'Song: Cozy', 'language': 'en-US', 'category': 'song'}, # works
    'en_female_f08_warmy_breeze': {'name': 'Song: Open Mic (Warmy Breeze)', 'language': 'en-US', 'category': 'song'}, # works
    'en_female_ht_f08_halloween': {'name': 'Song: Opera (Halloween)', 'language': 'en-US', 'category': 'song'}, # works
    'en_female_ht_f08_glorious': {'name': 'Song: Euphoric (Glorious)', 'language': 'en-US', 'category': 'song'}, # works
    'en_male_sing_funny_it_goes_up': {'name': 'Song: Hypetrain (It Goes Up)', 'language': 'en-US', 'category': 'song'}, # works
    'en_male_m03_lobby': {'name': 'Song: Jingle (Lobby)', 'language': 'en-US', 'category': 'song'}, # works
    'en_female_ht_f08_wonderful_world': {'name': 'Song: Melodrama (Wonderful World)', 'language': 'en-US', 'category': 'song'}, # works
    'en_female_ht_f08_newyear': {'name': 'Song: NYE 2023', 'language': 'en-US', 'category': 'song'}, # works
    'en_male_sing_funny_thanksgiving': {'name': 'Song: Thanksgiving', 'language': 'en-US', 'category': 'song'}, # works
    'en_male_m03_sunshine_soon': {'name': 'Song: Toon Beat (Sunshine Soon)', 'language': 'en-US', 'category': 'song'}, # works
    'en_female_f08_twinkle': {'name': 'Song: Pop Lullaby', 'language': 'en-US', 'category': 'song'}, # works
    'en_male_m2_xhxs_m03_silly': {'name': 'Song: Quirky Time', 'language': 'en-US', 'category': 'song'}, # works

    # French Voices
    'fr_001': {'name': 'French Male 1', 'language': 'fr-FR', 'category': 'standard'}, # not working
    'fr_002': {'name': 'French Male 2', 'language': 'fr-FR', 'category': 'standard'}, # not working

    # German Voices
    'de_001': {'name': 'German Female', 'language': 'de-DE', 'category': 'standard'}, # not working
    'de_002': {'name': 'German Male', 'language': 'de-DE', 'category': 'standard'}, # not working

    # Indonesian Voices
    'id_male_darma': {'name': 'Darma', 'language': 'id-ID', 'category': 'standard'}, # works
    'id_female_icha': {'name': 'Icha', 'language': 'id-ID', 'category': 'standard'}, # works
    'id_female_noor': {'name': 'Noor', 'language': 'id-ID', 'category': 'standard'}, # not working
    'id_male_putra': {'name': 'Putra', 'language': 'id-ID', 'category': 'standard'}, # works

    # Italian Voices
    'it_male_m18': {'name': 'Italian Male', 'language': 'it-IT', 'category': 'standard'}, # works

    # Japanese Voices
    'jp_001': {'name': 'Miho (美穂)', 'language': 'ja-JP', 'category': 'standard'}, # not working
    'jp_003': {'name': 'Keiko (恵子)', 'language': 'ja-JP', 'category': 'standard'}, # not working
    'jp_005': {'name': 'Sakura (さくら)', 'language': 'ja-JP', 'category': 'standard'}, # not working
    'jp_006': {'name': 'Naoki (直樹)', 'language': 'ja-JP', 'category': 'standard'}, # not working
    'jp_male_osada': {'name': 'モリスケ (Morisuke)', 'language': 'ja-JP', 'category': 'standard'}, # not working
    'jp_male_matsuo': {'name': 'モジャオ (Matsuo)', 'language': 'ja-JP', 'category': 'standard'}, # not working
    'jp_female_machikoriiita': {'name': 'まちこりーた (Machikoriiita)', 'language': 'ja-JP', 'category': 'standard'}, # works
    'jp_male_matsudake': {'name': 'マツダ家の日常 (Matsudake)', 'language': 'ja-JP', 'category': 'standard'}, # works 
    'jp_male_shuichiro': {'name': '修一朗 (Shuichiro)', 'language': 'ja-JP', 'category': 'standard'}, # works
    'jp_female_rei': {'name': '丸山礼 (Maruyama Rei)', 'language': 'ja-JP', 'category': 'standard'}, # works
    'jp_male_hikakin': {'name': 'ヒカキン (Hikakin)', 'language': 'ja-JP', 'category': 'standard'}, # works
    'jp_female_yagishaki': {'name': '八木沙季 (Yagi Saki)', 'language': 'ja-JP', 'category': 'standard'}, # not working

    # Korean Voices
    'kr_002': {'name': 'Korean Male 1', 'language': 'ko-KR', 'category': 'standard'}, # not working
    'kr_004': {'name': 'Korean Male 2', 'language': 'ko-KR', 'category': 'standard'}, # not working
    'kr_003': {'name': 'Korean Female', 'language': 'ko-KR', 'category': 'standard'}, # not working

    # Portuguese Voices
    'br_003': {'name': 'Júlia', 'language': 'pt-BR', 'category': 'standard'}, # not working
    'br_004': {'name': 'Ana', 'language': 'pt-BR', 'category': 'standard'}, # not working
    'br_005': {'name': 'Lucas', 'language': 'pt-BR', 'category': 'standard'}, # not working
    'pt_female_lhays': {'name': 'Lhays Macedo', 'language': 'pt-PT', 'category': 'standard'}, # works
    'pt_female_laizza': {'name': 'Laizza', 'language': 'pt-PT', 'category': 'standard'}, # works
    'pt_male_transformer': {'name': 'Optimus Prime (Portuguese)', 'language': 'pt-PT', 'category': 'character'}, # not working

    # Spanish Voices
    'es_002': {'name': 'Spanish Male', 'language': 'es-ES', 'category': 'standard'}, # not working
    'es_male_m3': {'name': 'Julio', 'language': 'es-ES', 'category': 'standard'}, # works
    'es_female_f6': {'name': 'Alejandra', 'language': 'es-ES', 'category': 'standard'}, # works
    'es_female_fp1': {'name': 'Mariana', 'language': 'es-ES', 'category': 'standard'}, # works
    'es_mx_002': {'name': 'Álex (Warm)', 'language': 'es-MX', 'category': 'standard'}, # not working
    'es_mx_male_transformer': {'name': 'Optimus Prime (Mexican)', 'language': 'es-MX', 'category': 'character'}, # not working
    'es_mx_female_supermom': {'name': 'Super Mamá', 'language': 'es-MX', 'category': 'character'} # not working
}