select * from {{ ref('stg_applications') }}
where amount_eur <= 0 or income_eur <= 0 or term_months <= 0
