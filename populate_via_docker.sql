-- Sample data population script for PostgreSQL
-- To be executed inside Docker container

-- Insert sample mentions
INSERT INTO mentions (source, content, created_at, author, url, engagement, brand, title, subreddit, post_id, news_source) VALUES
('reddit', 'I absolutely love Apple! Their products are amazing.', '2025-09-20 10:30:00', 'user_1', 'https://example.com/reddit/1001', 150, 'Apple', 'Apple Positive Mention', 'technology', 'post_1001', NULL),
('news', 'Samsung customer service is terrible, waited hours for a response.', '2025-09-21 14:15:00', 'user_2', 'https://example.com/news/2001', 89, 'Samsung', 'Samsung Negative Mention', NULL, NULL, 'TechNews'),
('reddit', 'Google announced a new product today.', '2025-09-22 09:45:00', 'user_3', 'https://example.com/reddit/1002', 45, 'Google', 'Google Neutral Mention', 'technology', 'post_1002', NULL),
('news', 'Microsoft is leading the industry with their innovative approach.', '2025-09-23 16:20:00', 'user_4', 'https://example.com/news/2002', 230, 'Microsoft', 'Microsoft Positive Mention', NULL, NULL, 'TechNews'),
('reddit', 'My Apple device broke after just a few months of use.', '2025-09-24 11:00:00', 'user_5', 'https://example.com/reddit/1003', 67, 'Apple', 'Apple Negative Mention', 'technology', 'post_1003', NULL);

-- Insert corresponding sentiment data
INSERT INTO sentiment (mention_id, polarity, subjectivity, compound_score, positive_score, negative_score, neutral_score) VALUES
(1, 0.8, 0.7, 0.6369, 0.692, 0.0, 0.308),
(2, -0.9, 0.8, -0.6249, 0.0, 0.625, 0.375),
(3, 0.0, 0.1, 0.0, 0.333, 0.0, 0.667),
(4, 0.6, 0.7, 0.4404, 0.473, 0.0, 0.527),
(5, -0.7, 0.8, -0.5719, 0.0, 0.412, 0.588);

-- Insert sample crisis alerts
INSERT INTO crisis_alerts (brand, description, severity, detected_at, status) VALUES
('Apple', 'Potential brand crisis: Negative sentiment spike detected for Apple', 0.75, '2025-09-24 12:00:00', 'investigating'),
('Samsung', 'Potential brand crisis: Customer service complaints increasing for Samsung', 0.65, '2025-09-23 08:30:00', 'new');

-- Insert sample influencers
INSERT INTO influencers (username, platform, followers, impact_score, brand_affinity, last_updated) VALUES
('tech_reviewer_01', 'YouTube', 250000, 0.85, 'Apple', '2025-09-20 10:00:00'),
('mobile_expert', 'Twitter', 150000, 0.78, 'Samsung', '2025-09-21 15:30:00'),
('google_fanboy', 'Instagram', 89000, 0.72, 'Google', '2025-09-22 09:15:00'),
('ms_enterprise', 'LinkedIn', 45000, 0.68, 'Microsoft', '2025-09-23 14:45:00');

-- Insert sample competitive metrics
INSERT INTO competitive_metrics (brand, competitor, sentiment_ratio, mention_count, engagement_rate, period_start, period_end) VALUES
('Apple', 'Samsung', 1.15, 125, 0.045, '2025-08-25 00:00:00', '2025-09-25 00:00:00'),
('Samsung', 'Apple', 0.87, 98, 0.038, '2025-08-25 00:00:00', '2025-09-25 00:00:00'),
('Google', 'Microsoft', 1.05, 76, 0.032, '2025-08-25 00:00:00', '2025-09-25 00:00:00'),
('Microsoft', 'Google', 0.95, 82, 0.029, '2025-08-25 00:00:00', '2025-09-25 00:00:00');