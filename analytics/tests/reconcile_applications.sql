select 1 as violation
where (select sum(applications) from {{ ref('fct_daily_lending') }})
   <> (select count(*) from {{ ref('stg_applications') }})
