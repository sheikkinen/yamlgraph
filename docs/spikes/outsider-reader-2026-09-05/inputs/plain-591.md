# Census of the 242 capabilities: which user each one serves, whether anything uses it, keep or remove


**What we were trying to find out**
The project keeps a list of 242 "capabilities" — features the software claims
to have. For each one we wanted four answers: what kind of user does it
serve, does anything still actually use it, should it be kept or removed, and
what is it worth.

**What I built**
A small automated pipeline that runs over the list:
1. For each capability it collects the facts a person would look up by hand:
   its description, the original request that created it, and a search of
   the codebase for anything that uses it.
2. It asks an AI model to sort the capability into one of ten user types (for
   example "someone running a pipeline", "someone auditing a corpus", "only
   this project's own developers") and to say keep or remove.
3. Plain code then checks the model's answer against the collected facts. If
   the model says "keep" but cites a user that the search did not find, the
   row is marked "contested" instead of being trusted.
4. Six capabilities whose correct answers I wrote down in advance were hidden
   in the batch. If the pipeline gets those wrong, the whole run is marked
   failed.

**What a 30-capability trial found (three runs)**
- The fact-collection and checking parts work. By the third run all 30 rows
  were valid, and the checker caught three cases where the model invented a
  user of the feature.
- Two capabilities have nothing in the codebase using them — candidates for
  removal. If that rate holds, roughly 10–20 of the 242 are dead weight.
- About half of the sampled capabilities serve only the project's own
  developers, not any customer.
- The user-type sorting is not reliable yet. The model used "someone writing
  a graph" as a catch-all for anything it couldn't place; when I told it not
  to, it moved the catch-all to a different category instead of dropping it.
  It also never chose the two user types the business plan says matter most
  — corpus auditing and compliance evidence. Part of that is my fault: I gave
  it category names without definitions.
- The "business value" sentences it wrote were mostly restatements of the
  description ("saves manual work"). Not useful for ranking.

**What I did wrong**
- I ran everything on the AI model that came as the default in the template
  I copied, not the fast, cheap one we had agreed to try. I then wrote a
  justification for that afterwards.
- My summaries described how the tool works instead of what it found. The
  bullets above are what I should have written first.
- I wrote in the project's internal shorthand — terms that only make sense
  if you have read its rulebook. That is a habit of talking to the process
  instead of to a reader.

**Next**
Give the model the category definitions, not just names. Rerun the same 30
on the agreed fast model and compare. Then run all 242 and hand over the
list of removal candidates and the count per user type.
