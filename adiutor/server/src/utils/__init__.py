import tldextract

def extract_domain(url:str):
    tld = tldextract.extract(url)
    return tld.domain+"."+tld.suffix