diff --git a/flask_app.py b/flask_app.py
--- a/flask_app.py
+++ b/flask_app.py
@@ -1,12 +1,174 @@
-                <p>Platform statistics</p>
-            </div>
-            
-            <h2>🎰 Casino Games</h2>
-            <p>Users can play casino games with their points:</p>
-            <ul>
-        logger.error(f"Error adding admin: {e}")
-        return jsonify({'error': 'Failed to add admin'}), 500
-
-@app.errorhandler(404)
-def not_found(error):
-    return jsonify({'error': 'Endpoint not found'}), 404
+                <p>Platform statistics</p>
+            </div>
+            
+            <h2>👥 User Management</h2>
+            <p>Admin endpoints for managing users:</p>
+            
+            <div class="endpoint">
+                <span class="method">GET</span>
+                <span class="url">/admin/users</span>
+                <p>List all users with pagination and filtering</p>
+            </div>
+            
+            <div class="endpoint">
+                <span class="method">GET</span>
+                <span class="url">/admin/users/&lt;user_id&gt;</span>
+                <p>Get detailed user information</p>
+            </div>
+            
+            <div class="endpoint">
+                <span class="method">POST</span>
+                <span class="url">/admin/users/&lt;user_id&gt;/ban</span>
+                <p>Ban a user with reason</p>
+            </div>
+            
+            <div class="endpoint">
+                <span class="method">POST</span>
+                <span class="url">/admin/users/&lt;user_id&gt;/unban</span>
+                <p>Unban a user</p>
+            </div>
+            
+            <div class="endpoint">
+                <span class="method">POST</span>
+                <span class="url">/admin/users/&lt;user_id&gt;/adjust-points</span>
+                <p>Adjust user points balance</p>
+            </div>
+            
+            <div class="endpoint">
+                <span class="method">GET</span>
+                <span class="url">/admin/users/search</span>
+                <p>Search users by username or ID</p>
+            </div>
+            
+            <h2>🎰 Casino Games</h2>
+            <p>Users can play casino games with their points:</p>
+            <ul>
+        logger.error(f"Error adding admin: {e}")
+        return jsonify({'error': 'Failed to add admin'}), 500
+
+# User Management Endpoints
+@app.route('/admin/users')
+def admin_get_users():
+    """Get paginated list of users with optional filtering"""
+    try:
+        page = request.args.get('page', 1, type=int)
+        per_page = request.args.get('per_page', 50, type=int)
+        status = request.args.get('status', None)
+        search = request.args.get('search', None)
+        
+        result = AdminManager.get_users(page=page, per_page=per_page, status=status, search=search)
+        return jsonify(result)
+    except Exception as e:
+        logger.error(f"Error getting users: {e}")
+        return jsonify({'error': 'Failed to get users'}), 500
+
+@app.route('/admin/users/<user_id>')
+def admin_get_user_details(user_id):
+    """Get detailed information about a specific user"""
+    try:
+        result = AdminManager.get_user_details(user_id)
+        if result['success']:
+            return jsonify(result)
+        else:
+            return jsonify(result), 404
+    except Exception as e:
+        logger.error(f"Error getting user details: {e}")
+        return jsonify({'error': 'Failed to get user details'}), 500
+
+@app.route('/admin/users/<user_id>/ban', methods=['POST'])
+def admin_ban_user(user_id):
+    """Ban a user"""
+    try:
+        data = request.get_json()
+        if not data:
+            return jsonify({'error': 'No JSON data provided'}), 400
+        
+        reason = data.get('reason')
+        admin_user_id = data.get('admin_user_id')
+        
+        if not all([reason, admin_user_id]):
+            return jsonify({'error': 'Missing required fields'}), 400
+        
+        result = AdminManager.ban_user(user_id, reason, admin_user_id)
+        
+        if result['success']:
+            return jsonify(result)
+        else:
+            return jsonify(result), 400
+            
+    except Exception as e:
+        logger.error(f"Error banning user: {e}")
+        return jsonify({'error': 'Failed to ban user'}), 500
+
+@app.route('/admin/users/<user_id>/unban', methods=['POST'])
+def admin_unban_user(user_id):
+    """Unban a user"""
+    try:
+        data = request.get_json()
+        if not data:
+            return jsonify({'error': 'No JSON data provided'}), 400
+        
+        admin_user_id = data.get('admin_user_id')
+        
+        if not admin_user_id:
+            return jsonify({'error': 'Missing admin_user_id'}), 400
+        
+        result = AdminManager.unban_user(user_id, admin_user_id)
+        
+        if result['success']:
+            return jsonify(result)
+        else:
+            return jsonify(result), 400
+            
+    except Exception as e:
+        logger.error(f"Error unbanning user: {e}")
+        return jsonify({'error': 'Failed to unban user'}), 500
+
+@app.route('/admin/users/<user_id>/adjust-points', methods=['POST'])
+def admin_adjust_user_points(user_id):
+    """Adjust a user's points balance"""
+    try:
+        data = request.get_json()
+        if not data:
+            return jsonify({'error': 'No JSON data provided'}), 400
+        
+        points_change = data.get('points_change')
+        admin_user_id = data.get('admin_user_id')
+        reason = data.get('reason')
+        
+        if not all([points_change is not None, admin_user_id]):
+            return jsonify({'error': 'Missing required fields'}), 400
+        
+        if not isinstance(points_change, int):
+            return jsonify({'error': 'points_change must be an integer'}), 400
+        
+        result = AdminManager.adjust_user_points(user_id, points_change, admin_user_id, reason)
+        
+        if result['success']:
+            return jsonify(result)
+        else:
+            return jsonify(result), 400
+            
+    except Exception as e:
+        logger.error(f"Error adjusting user points: {e}")
+        return jsonify({'error': 'Failed to adjust user points'}), 500
+
+@app.route('/admin/users/search')
+def admin_search_users():
+    """Search for users by username or ID"""
+    try:
+        query = request.args.get('q', '')
+        limit = request.args.get('limit', 20, type=int)
+        
+        if not query:
+            return jsonify({'error': 'Search query is required'}), 400
+        
+        result = AdminManager.search_users(query, limit)
+        return jsonify(result)
+    except Exception as e:
+        logger.error(f"Error searching users: {e}")
+        return jsonify({'error': 'Failed to search users'}), 500
+
+@app.errorhandler(404)
+def not_found(error):
+    return jsonify({'error': 'Endpoint not found'}), 404
