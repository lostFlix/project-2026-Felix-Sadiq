# build_products.py
# what this does (in short):
# 1) read the raw scrape (all 4 shops, every search result) from data/raw/products_raw.csv
# 2) keep only products we care about and give each one a product_type (keyword rules)
# 3) turn the size text ("2 x 125g", "1kg", "10 Stueck") into grams -> price per kg
# 4) add nutrition per 100 g: real values from the product page (Migros/Coop) or from
#    Open Food Facts (Lidl/Aldi) if we have them, otherwise a reference value for this
#    product type (Swiss nutrition table BLV)
# 5) add the columns we need for our questions F1-F4 and save data/processed/products_clean.csv
import re
import numpy as np
import pandas as pd

# Reference nutrition per 100 g (kcal, protein, fat, carbs).
# Source: Schweizer Naehrwerttabelle (BLV), unless marked "measured" (mean of our own
# Migros/Coop product pages from 25.11.2026).
REF = {
 'haehnchenbrust':   (107, 24.6, 1.0, 0.0, 'BLV: Poulet, Brust, ohne Haut, roh'),
 'poulet_aufschnitt':(107, 24.6, 1.0, 0.0, 'BLV: Poulet, Brust, ohne Haut, roh (Aufschnitt-Naeherung)'),
 'trutenbrust':      (108, 24.0, 1.3, 0.0, 'BLV: Truthahn, Brust, roh'),
 'schinken':         (196, 25.4, 9.9, 1.4, 'BLV: Rollschinken, gekocht'),
 'eier':             (142, 11.9, 10.3, 0.3, 'BLV: Huehnerei, ganz, roh'),
 'thunfisch':        (117, 25.6, 1.6, 0.0, 'BLV: Thon in Wasser, abgetropft'),
 'thunfisch_oel':    (186, 27.6, 8.4, 0.0, 'BLV: Thon in Oel, abgetropft'),
 'lachs':            (182, 19.7, 11.5, 0.0, 'BLV: Lachs, wild, roh'),
 'lachs_rauch':      (167, 23.2, 8.2, 0.0, 'BLV: Lachs, geraeuchert'),
 'magerquark':       (61, 10.6, 0.2, 4.2, 'BLV: Quark, nature, mager'),
 'quark':            (99, 9.4, 5.0, 4.1, 'BLV: Quark, nature, halbfett'),
 'skyr':             (60, 11.5, 0.2, 3.2, 'measured: Skyr nature Migros+Coop'),
 'joghurt':          (66, 3.9, 3.6, 4.5, 'BLV: Joghurt, nature'),
 'huettenkaese':     (100, 12.4, 4.5, 2.4, 'BLV: Huettenkaese, nature'),
 'emmentaler':       (408, 28.4, 32.6, 0.0, 'BLV: Emmentaler, vollfett'),
 'gruyere':          (396, 26.4, 32.0, 0.0, 'BLV: Greyerzer, vollfett'),
 'parmesan':         (370, 34.9, 25.6, 0.0, 'BLV: Parmesan'),
 'mozzarella':       (256, 19.5, 19.5, 0.7, 'BLV: Mozzarella'),
 'light_mozzarella': (152, 20.0, 7.5, 1.0, 'measured: Coop Mollini -58% Fett'),
 'feta':             (256, 16.0, 20.7, 1.4, 'BLV: Feta (Kuhmilch)'),
 'high_protein':     (81.5, 10.5, 1.65, 5.95, 'measured: High-Protein-Pudding Migros+Coop (Mittel)'),
 'high_protein_kaese':(213, 33.0, 9.0, 0.0, 'measured: High-Protein-Kaesescheiben Migros+Coop'),
 'tofu':             (126, 15.3, 5.6, 2.8, 'BLV: Tofu, fest, nature'),
 'fleischersatz':    (130.7, 21.3, 2.83, 2.07, 'measured: Planted (Migros, Coop) + Quorn (Migros), Mittel'),
 'huelsenfruechte':  (324, 24.4, 1.5, 44.8, 'BLV: Linse, getrocknet'),
 'huelsen_gekocht':  (116, 8.9, 0.5, 15.6, 'BLV: Linse, gekocht (Konserve-Naeherung)'),
 'brot_weiss':       (242, 8.5, 0.8, 48.9, 'BLV: Weissbrot'),
 'brot_vollkorn':    (213, 8.6, 1.3, 38.3, 'BLV: Weizenvollkornbrot'),
 'brot':             (234, 9.5, 1.2, 44.3, 'BLV: Ruchbrot'),
 'aepfel':           (55, 0.3, 0.3, 11.7, 'BLV: Apfel, roh'),
 'bananen':          (95, 1.1, 0.3, 21.0, 'BLV: Banane, roh'),
 'avocado':          (144, 1.8, 14.2, 0.8, 'BLV: Avocado, roh'),
 'tomaten':          (21, 0.8, 0.3, 3.2, 'BLV: Tomate, roh'),
 'gurke':            (14, 0.7, 0.1, 2.0, 'BLV: Gurke, roh'),
 'salat':            (14, 1.3, 0.2, 1.1, 'BLV: Kopfsalat, roh'),
 'karotten':         (38, 0.8, 0.3, 6.6, 'BLV: Karotte, roh'),
 'peperoni':         (26, 0.85, 0.35, 3.9, 'BLV: Peperoni gruen/rot, roh (Mittel)'),
 'broccoli':         (31, 3.0, 0.4, 2.4, 'BLV: Broccoli, roh'),
 'zwiebeln':         (39, 1.3, 0.2, 7.0, 'BLV: Zwiebel, roh'),
}


# 1) read raw data, one row per product (same product can show up for 2 search words)
d = pd.read_csv('data/raw/products_raw.csv', dtype=str).fillna('')
d = d.drop_duplicates('url').copy()
n = d['product'].str.lower()

# 2) keyword rules: words we never want (EXCL) and words that decide the product_type (first match wins)
EXCL = r"mayo|protein water|mineralwasser|daily|wrap thon|ofengemüse|red thai|in rotem curry|kichererbsencurry|im teig|balsamico|sablés|special k|peak punk|linsen mit gemüse|linsen burger|schnelle mischung|frischkäse|alternative zu lachs|flachbohnen|eisbecher|rieg\b|shots|healthy fit|sprossen|codegotto|crispy|paniert|sticks|blévita|risotto|börek|crème fraîche|creme fraiche|caffè|caffe|pringles|tomatenmark|tomatenstück|polpa|streich|fideli|gnocchi|knopf|suppe|eintopf|topf\b|waffel|kontaktlinse|linsenlö|quetschbeutel|porridge|oliven|pesto|antipasti|passiert|gehackt|geschält|pelati|sugo|fixe|hörnli|berliner|globi|aktifit|schoggi|croissant|gipfeli|gefüllt|fleischkäse|backbeutel|tar\b|tartar|getrocknet|eingelegt|geröstet|gewürzmischung|gewürzsalz|mc cormick|mccormick|salsa|pet\b|uht|le gusto|wonnemeyer|konserve|püree|chili con|aufbackbrötchen mit|kaffee|espresso|kakao|chips|schoko|choceur|tafel|kuchen|cake|brei|hipp|pizza|sauce|sosse|dressing|ketchup|saft|nektar|smoothie|drink|shake|riegel|bar\b|müesli|muesli|loops|glace|eis\b|hund|katze|tier|kollagen|whey|pulver|shampoo|duschgel|creme|lotion|aufstrich|crackers|cracker|snack|nuggets im teig|tiramisu|dessert|likör|nudeln|teigwaren|tagliatelle|spätzli|pasta|lasagne|ravioli|tortellini|fertiggericht|bowl|sandwich|tramezzini|weggli lyoner|kartoffel|gratin|strudel|mus\b|chutney|konfitüre|gelee|tee\b|sirup|gummi|bonbon|kaugummi|candy|toaster|zahnpasta|deo|kerze|spiel|figur|puppe|ostern|weihnacht|samichlaus|adventskalender|wurst|salami|cervelat|speck|lyoner|mortadella|chorizo|baby|kind"
rules=[
 # protein bread / rolls / wraps are still bread -> must come before skyr and high_protein
 ('brot', r"(protein|skyr).*(brot|brötli|brötchen|wrap)|(brot|brötchen).*protein"),
 ('poulet_aufschnitt', r"(poulet|huhn|hähnchen|chicken).*(aufschnitt|hauchdünn|geschnitten|scheiben|gekocht|geräuchert|smoky|curry|paprika|grill|delikatess)|(aufschnitt|hauchdünn).*(poulet|huhn)"),
 ('trutenbrust', r"trute|truthahn|turkey"),
 ('haehnchenbrust', r"pouletbrust|poulet brust|pouletfilet|poulet-filet|pouletschnitzel|poulet minutenschnitzel|poulet-minutenschnitzel|pouletbrust-|poulet geschnetzeltes|pouletgeschnetzeltes|pouletfilet-geschnetzeltes|poulet-geschnetzeltes|pouletwürfel|pouletbrustwürfel"),
 ('schinken', r"schinken|prosciutto|jambon"),
 ('magerquark', r"magerquark|quark mager|speisequark mager"),
 ('skyr', r"skyr"),
 ('huettenkaese', r"hüttenkäse|cottage"),
 ('high_protein', r"(high.?protein|protein)(?!.*milch)"),
 ('quark', r"quark"),
 ('joghurt', r"joghurt|jogurt|yogurt|yoghurt"),
 ('emmentaler', r"emmentaler|emmental"),
 ('gruyere', r"gruyère|gruyere|greyerzer"),
 ('parmesan', r"parmigiano|parmesan|grana padano"),
 ('light_mozzarella', r"mozzarella.*(light|leicht|-58|fettreduziert)|(light|leicht).*mozzarella"),
 ('mozzarella', r"mozzarella"),
 ('feta', r"feta|salatkäse|hirtenkäse"),
 ('eier', r"\beier\b|freilandeier|\bei\b"),
 ('thunfisch', r"thunfisch|\bthon\b"),
 ('lachs', r"lachs|salmon"),
 ('tofu', r"tofu"),
 ('fleischersatz', r"planted|quorn|tempeh|seitan|vegane alternative|vegetarische alternative|veganer mix|vegan.*(geschnetzelt|hack|burger|schnitzel|filet|würfel|nuggets|poulet|chicken)"),
 ('huelsenfruechte', r"linsen|kichererbsen|bohnen"),
 ('brot', r"brot|toast|zopf|baguette|weggli|brötli|bürli|semmel|laugen|wrap|tortilla|pita|fladen|ciabatta|gipfeli|croissant"),
 ('aepfel', r"äpfel|apfel\b|^apfel|gala|golden|braeburn|jazz|pink lady|granny"),
 ('bananen', r"banane"),
 ('avocado', r"avocado"),
 ('tomaten', r"tomate|cherry|datterini|rispen"),
 ('gurke', r"gurke"),
 ('salat', r"salat|lattich|eisberg|rucola|nüsslisalat|kopfsalat|eichblatt|batavia"),
 ('karotten', r"karotte|rüebli"),
 ('peperoni', r"peperoni|paprika"),
 ('broccoli', r"broccoli|brokkoli"),
 ('zwiebeln', r"zwiebel"),
]
cat={'poulet_aufschnitt':'tierisch','trutenbrust':'tierisch','haehnchenbrust':'tierisch','schinken':'tierisch','eier':'tierisch','thunfisch':'tierisch','lachs':'tierisch',
 'magerquark':'milch','skyr':'milch','huettenkaese':'milch','quark':'milch','joghurt':'milch','emmentaler':'milch','gruyere':'milch','parmesan':'milch','mozzarella':'milch','light_mozzarella':'milch','feta':'milch',
 'high_protein':'high_protein','tofu':'pflanzlich','fleischersatz':'pflanzlich','huelsenfruechte':'pflanzlich','brot':'backwaren',
 'aepfel':'obst','bananen':'obst','avocado':'obst','tomaten':'gemuese','gurke':'gemuese','salat':'gemuese','karotten':'gemuese','peperoni':'gemuese','broccoli':'gemuese','zwiebeln':'gemuese'}
# exceptions where exclusion words are fine
ok_excl={'high_protein':r"drink|shake|riegel|bar\b|pulver|whey|chips|müesli|loops|aufstrich|glace|eis\b",}
def classify(name, term):
    for t,rx in rules:
        if re.search(rx,name):
            # vegetables/fruit/bread names that also hit exclusion -> drop
            if re.search(EXCL,name):
                # allow 'salatkäse' etc handled; allow 'eiersalat'? -> drop
                return None
            return t
    return None
d['product_type'] = [classify(x, t) for x, t in zip(n, d.search_term)]
d = d[d.product_type.notna()].copy()
d['category'] = d.product_type.map(cat)

# 3) package size in grams
def grams(size, name):
    s=(size or '').lower().replace(',', '.') if isinstance(size,str) else ''
    src=s if re.search(r'\d',s) else str(name).lower()
    m=re.search(r'(\d+)\s*x\s*([\d.]+)\s*(kg|g|ml|l)\b',src)
    if m:
        k,v,u=int(m.group(1)),float(m.group(2)),m.group(3); f={'kg':1000,'g':1,'ml':1,'l':1000}[u]; return k*v*f,'pack'
    m=re.search(r'([\d.]+)\s*(kg|g|ml|cl|l)\b',src)
    if m:
        v,u=float(m.group(1)),m.group(2); f={'kg':1000,'g':1,'ml':1,'cl':10,'l':1000}[u]; return v*f,'pack'
    m=re.search(r'(\d+)\s*(stück|stk|st\b|er\b)',src)
    if m: return int(m.group(1)), 'piece'
    return np.nan,''
g=[grams(s,n) for s,n in zip(d.size_text,d['product'])]
d['package_amount']=[x[0] for x in g]; d['package_unit']=[x[1] for x in g]
d['price_chf']=pd.to_numeric(d.price_chf,errors='coerce')
# eggs: pieces -> grams (assumption 60 g per egg)
egg=(d.product_type=='eier')&(d.package_unit=='piece')
d['package_g']=np.where(d.package_unit=='pack',d.package_amount,np.where(egg,d.package_amount*60,np.nan))
d['egg_weight_assumed']=egg
# unit price fallback from text (CHF per kg)
def unit_kg(t):
    t=str(t).replace(',', '.')
    m=re.search(r'([\d.]+)\s*/\s*100\s*g',t) or re.search(r'100\s*g\s*=\s*([\d.]+)',t) or re.search(r'CHF\s*([\d.]+)\s*/\s*100\s*g',t)
    if m: return float(m.group(1))*10
    m=re.search(r'([\d.]+)\s*/\s*(1\s*)?kg',t,re.I) or re.search(r'1\s*kg\s*=\s*([\d.]+)',t,re.I) or re.search(r'CHF\s*([\d.]+)\s*/\s*1\s*kg',t,re.I)
    if m: return float(m.group(1))
    return np.nan
d['price_per_kg']=(d.price_chf/d.package_g*1000).round(2)
# if the shop's own unit price disagrees a lot (>15 %), trust the shop (e.g. cheese priced per 100 g at the counter)
shop_kg=d['unit_price_text'].map(unit_kg)
bad=shop_kg.notna()&d.price_per_kg.notna()&((d.price_per_kg/shop_kg-1).abs()>0.15)
d.loc[bad,'price_per_kg']=shop_kg[bad]
fb=d.price_per_kg.isna()
d.loc[fb,'price_per_kg']=d.loc[fb,'unit_price_text'].map(unit_kg)
d['promo']=d.promo.astype(str).str.strip().eq('1')

# 4) + 5)
# clean product names (Migros promo prefix)
d['product']=d['product'].str.replace(r'^statt [\d.]+ .*?(Franken|Rappen)[^,]*,\s*','',regex=True).str.strip()
d=d[~d['product'].str.contains(r"lip balm|l'oréal|laque|nyx|regionaler preis",case=False,regex=True)]
# 'salat' in the name of a non-salad product = ready-made salad dish -> drop
d=d[~((d.product_type!='salat')&d['product'].str.contains(r'salat(?!käse)',case=False,regex=True)&(d.product_type!='feta'))]
# green beans are vegetables, not pulses
d=d[~((d.product_type=='huelsenfruechte')&d['product'].str.contains(r'grüne|grün\b|fein|bohnen grün|brech',case=False,regex=True)&~d['product'].str.contains('linsen',case=False))]
# small seasoned chicken-breast packs (<=200 g) are cold cuts
sm=(d.product_type=='haehnchenbrust')&(d.package_g<=200)&d['product'].str.contains(r'gewürzt|pfeffer|hauchdünn|gekocht',case=False,regex=True)&~d['product'].str.contains(r'stück|spiess',case=False,regex=True)
d.loc[sm,'product_type']='poulet_aufschnitt'
d=d[d.price_chf.notna()]
# which reference row?
def refkey(t,name):
    n=name.lower()
    if t=='thunfisch' and re.search(r'öl|oel|olive',n): return 'thunfisch_oel'
    if t=='lachs' and re.search(r'rauch|geräuchert|smoked',n): return 'lachs_rauch'
    if t=='high_protein' and re.search(r'käse|kaese|scheiben|reib',n): return 'high_protein_kaese'
    if t=='huelsenfruechte' and not (re.search(r'getrocknet|trocken',n) or (re.search(r'linsen',n) and not re.search(r'dose|konserve|gekocht|sous-vide|vegan|mit ',n))): return 'huelsen_gekocht'
    if t=='brot':
        if re.search(r'vollkorn|graham',n): return 'brot_vollkorn'
        if re.search(r'toast|weiss|zopf|baguette|weggli|brötli|laugen|ciabatta|tortilla|wrap|pita|semmel|bürli',n): return 'brot_weiss'
        return 'brot'
    return t
d['ref_key']=[refkey(t,n) for t,n in zip(d.product_type,d['product'])]
# small lentil packs (< 300 g) are usually cans -> cooked values
d.loc[(d.ref_key=='huelsenfruechte')&(d.package_g<300),'ref_key']='huelsen_gekocht'
for i,c in enumerate(['kcal_100g','protein_100g','fat_100g','carbs_100g']):
    d[c]=d.ref_key.map(lambda k:REF[k][i])
d['nutrition_source']='reference: '+d.ref_key.map(lambda k:REF[k][4])
# overwrite with real product-page values (Migros/Coop pages we opened one by one on 25.11,
# first only the top products, then all protein products)
pages = pd.read_csv('data/raw/product_pages_nutrition.csv').drop_duplicates('url')
pages = pages[pages.protein_100g.notna()].set_index('url')   # some pages show no protein -> keep the reference value
m = d.url.isin(pages.index)
for c in ['kcal_100g', 'protein_100g', 'fat_100g', 'carbs_100g']:
    d.loc[m, c] = d.loc[m, 'url'].map(pages[c])
d.loc[m, 'nutrition_source'] = 'product_page'
# real values show: 'Bohnen' with < 3 g protein are green beans (a vegetable), not pulses -> drop
d = d[~((d.product_type == 'huelsenfruechte') & (d.protein_100g < 3))]
# Lidl + Aldi don't show nutrition online -> real label values from Open Food Facts
# we matched by name + brand by hand, match = exact or likely (see note column)
off = pd.read_csv('data/raw/openfoodfacts_nutrition.csv').set_index('url')
m = d.url.isin(off.index)
for c in ['kcal_100g', 'protein_100g', 'fat_100g', 'carbs_100g']:
    d.loc[m, c] = d.loc[m, 'url'].map(off[c])
d.loc[m, 'nutrition_source'] = 'openfoodfacts (' + d.loc[m, 'url'].map(off['match']) + ')'
old_all = pd.read_csv('data/raw/first_dataset_56.csv')   # only used for the dog-food joke row
# add the dog-food joke row from the first dataset
dog=old_all[old_all.joke==True].reset_index(drop=True)
dog_row=dict(store='migros',search_term='hundefutter',product=dog['product'][0],price_chf=dog.price_chf[0],size_text='3kg',unit_price_text='',promo=False,url=dog.url[0],
   product_type='hundefutter',category='joke',package_g=3000.0,price_per_kg=round(dog.price_chf[0]/3,2),kcal_100g=dog.kcal_100g[0],protein_100g=dog.protein_100g[0],
   fat_100g=dog.fat_100g[0],carbs_100g=dog.carbs_100g[0],nutrition_source='product_page (Futtermittel: nur Protein/Fett angegeben, kcal geschaetzt)',egg_weight_assumed=False)
d=pd.concat([d,pd.DataFrame([dog_row])],ignore_index=True)
d['joke']=d.product_type.eq('hundefutter')
d['vegan']=d['product'].str.contains('vegan',case=False)|d.product_type.isin(['tofu'])
d['price_source']='scraped'
d['date_collected']='2026-11-25'
# derived columns (Fragen F1-F4)
d['protein_pack_g']=(d.protein_100g*d.package_g/100).round(1)
d['chf_per_100g_protein']=(d.price_per_kg/10/d.protein_100g*100).round(2)
d['protein_kcal_share']=(d.protein_100g*4/d.kcal_100g).round(3)
for x in [5,10,20]: d[f'under_{x}']=d.price_chf<x
cols=['store','product_type','category','product','price_chf','size_text','package_g','price_per_kg','promo',
      'kcal_100g','protein_100g','fat_100g','carbs_100g','nutrition_source','egg_weight_assumed','vegan','joke',
      'protein_pack_g','chf_per_100g_protein','protein_kcal_share','under_5','under_10','under_20',
      'search_term','unit_price_text','price_source','url','date_collected']
d=d[cols].sort_values(['category','product_type','store','price_per_kg'])
d.to_csv('data/processed/products_clean.csv',index=False)
print('clean rows:',len(d))
print(d.groupby('store').size())
