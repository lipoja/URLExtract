## URLFinder
URLFinder is python class for collecting URLs from given text. 

### How does it work
It tries to find any occurrence of TLD in given text. If TLD is found it starts from that position to expand boundaries to both sides searching for "stop character" (usually whitespace, comma, single or double quote).

### Requirements
- IDNA for converting links to IDNA format  
```
pip install idna
```  

### Example
 You can look at example program *find_urls.py*.   
 But everything you need to know is this:
```python
from URLFinder import URLFinder

finder = URLFinder()
urls = finder.find_urls("Text with URLs. Let's have URL janlipovsky.cz as an example.")
print(urls) # prints: ['janlipovsky.cz']
```

### License
This piece of code is licensed under The MIT License.
