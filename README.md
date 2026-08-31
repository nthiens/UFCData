## Table of Contents

* [Installation](#installation)
* [Getting Started](#getting-started)
* [Available Data](#available-data)
* [Functions](#functions)

  * [Data Access](#data-access)

    * [`get_data()`](#get_data)
  * [Search](#search)

    * [`search(data, column, query, matches=1)`](#searchdata-column-query-matches1)
  * [Ratings](#ratings)

    * [`get_elo(r=1500, k=30, s=400)`](#get_elor1500-k30-s400)
  * [Fighter Analysis](#fighter-analysis)

    * [`get_fighter_history(fighter_link)`](#get_fighter_historyfighter_link)
    * [`get_fighter_statistic(fighter_link, r=1500, k=30, s=400)`](#get_fighter_statisticfighter_link-r1500-k30-s400)
  * [Helper Functions](#helper-functions)

    * [`convert_odds(odds)`](#convert_oddsodds)
    * [`convert_gender(gender)`](#convert_gendergender)
    * [`convert_weight(weight)`](#convert_weightweight)
    * [`mirror(df, cols_1, cols_2, in_order=True)`](#mirrordf-cols_1-cols_2-in_ordertrue)
  * [Model Evaluation](#model-evaluation)

    * [`train_test_split(fights_df, test_size=0.2)`](#train_test_splitfights_df-test_size02)
    * [`get_expanding_window(fights_df, folds, test_size)`](#get_expanding_windowfights_df-folds-test_size)
  * [Plotting](#plotting)

    * [`plot_fight_graph(fighter_link, degree, notebook=False)`](#plot_fight_graphfighter_link-degree-notebookfalse)
    * [`plot_body(...)`](#plot_bodyminimum-maximum-title-head-body-leg-head_label-body_label-leg_label-suffix)
    * [`plot_line_graph(...)`](#plot_line_graphtitle-x_label-x_values-y_label-y_values-averagetrue)
    * [`plot_bar_graph(...)`](#plot_bar_graphtitle-x_label-x_values-y_label-y_values-averagetrue)
* [Example: Temporal Model Evaluation](#example-temporal-model-evaluation)
* [Data Collection](#data-collection)
* [Data and Temporal Leakage](#data-and-temporal-leakage)
