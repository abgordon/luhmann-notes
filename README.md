# Luhmann notes


"Early in his academic career, Luhmann realized that a note was only as valuable as its context – its network of associations, relationships, and connections to other information."

Inspired by [this article](https://praxis.fortelabs.co/how-to-take-smart-notes/)

Run a sql container and store extensible notes. TODO: This shouldn't run as a container because inevitably the container will go down and you will lose all of your work. I need to buy an amazon sql server...

### works in progress

- web server that provides an interface to the notes 
- graphs! interactive ones! This will be a huge PITA because the web server will be in django and only d3 allows for a truly interactive browser experience! Otherwise, it will just be statically rendered graph images. But wait, d3 totally sucks because a) it's javascript b) the API is weird and clunky
- rewrite the backend to use neo4j because of the above. Then I can just embed the browser panel into a page, probably, and see all the data that way