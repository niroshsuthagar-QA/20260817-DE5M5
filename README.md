#20260817-DE5M5

```python
# Creating and using a function to enrich the data by adding in the time a book was on loan.
data_enriched = na_dropped_data.copy()

def enrich_dateDuration(colA, colB, df=data_enriched):
    """
    Takes the two input columns and the dataframe to create a new column date_delta which is the difference, in days, between colA and colB.
    
    Note: ColA should be the highest of the expected date columns.
    """
    df['date_delta'] = (df[colA]-df[colB]).dt.days
    return df.head()

enrich_dateDuration(df=data_enriched, colA='Book Returned', colB='Book checkout')
```
