# backbone_of_code brings in the other file into this code, prgm makes it easier to refer to instead of rewriting the full py file
import backbone_of_code as prgrm
from http.server import *

# ---------------------------------------------------------
# The following code inputs the data into the databases and gets the data into the website :)
# ---------------------------------------------------------     

hostName = "localhost"
serverPort = 8080

if __name__ == '__main__':
    db = prgrm.DefenceDatabase()
    execute = prgrm.DataFetcher()

    # Generate the website    
    loader = prgrm.LoadWebsite("defence.db", "nea_website_template.html")
    loader.generate_html("index.html")
    
