<?php
/**
 * CRUD Controller Scaffold for Laravel API
 * Copy this template, replace <Resource> with your model name (e.g., Vehicle, Facility, Booking)
 * Then fill in validation rules and authorization logic specific to your resource.
 */

namespace App\Http\Controllers\Api;

use App\Models\<Resource>;
use Illuminate\Http\Request;

class <Resource>Controller
{
    /**
     * Display a listing of the resource (paginated or all).
     */
    public function index()
    {
        $items = <Resource>::with(['relation1', 'relation2'])->get();

        return response()->json([
            '<resources>' => $items,
        ]);
    }

    /**
     * Store a newly created resource in storage.
     */
    public function store(Request $request)
    {
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'description' => 'nullable|string',
            'is_active' => 'boolean',
            // Add more validation rules as needed
        ]);

        $item = <Resource>::create($validated);

        return response()->json([
            'message' => '<Resource> created successfully',
            '<resource>' => $item->load(['relation1']),
        ], 201);
    }

    /**
     * Display the specified resource.
     */
    public function show(<Resource> $<resource>)
    {
        return response()->json([
            '<resource>' => $<resource>->load(['relation1', 'relation2']),
        ]);
    }

    /**
     * Update the specified resource in storage.
     */
    public function update(Request $request, <Resource> $<resource>)
    {
        // Optional: Authorization check
        // if ($request->user()->id !== $<resource>->user_id && !$request->user()->isAdmin()) {
        //     return response()->json(['message' => 'Unauthorized'], 403);
        // }

        $validated = $request->validate([
            'name' => 'string|max:255',
            'description' => 'nullable|string',
            'is_active' => 'boolean',
        ]);

        $<resource>->update($validated);

        return response()->json([
            'message' => '<Resource> updated successfully',
            '<resource>' => $<resource>->load(['relation1']),
        ]);
    }

    /**
     * Remove the specified resource from storage.
     */
    public function destroy(Request $request, <Resource> $<resource>)
    {
        // Optional: Authorization check
        // if ($request->user()->id !== $<resource>->user_id && !$request->user()->isAdmin()) {
        //     return response()->json(['message' => 'Unauthorized'], 403);
        // }

        $<resource>->delete();

        return response()->json([
            'message' => '<Resource> deleted successfully',
        ]);
    }
}
