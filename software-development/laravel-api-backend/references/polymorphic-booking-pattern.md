# Polymorphic Booking Pattern for Laravel

## Use Case
Single `Booking` table that can reference multiple resource types (e.g., `Vehicle` OR `Facility`).
Example: Sekolah wants to track both vehicle rentals and facility reservations in one unified interface.

## Schema Design

### Migration: Bookings Table (Polymorphic)
```php
Schema::create('bookings', function (Blueprint $table) {
    $table->id();
    $table->foreignId('user_id')->constrained()->onDelete('cascade');
    $table->foreignId('category_id')->constrained()->onDelete('cascade');
    
    // Polymorphic fields (instead of vehicle_id OR facility_id)
    $table->string('bookable_type');        // e.g., "App\Models\Vehicle"
    $table->unsignedBigInteger('bookable_id');
    
    // Domain-specific fields
    $table->string('driver')->nullable();
    $table->string('purpose')->nullable();
    $table->string('organizer')->nullable();
    $table->string('event_name')->nullable();
    
    // Common fields
    $table->string('responsible_person');
    $table->string('responsible_phone');
    $table->date('date_from');
    $table->date('date_to');
    $table->time('time_from');
    $table->time('time_to');
    $table->enum('status', ['pending', 'approved', 'rejected', 'completed'])->default('pending');
    $table->timestamps();
});
```

## Models: morphMany / morphTo

### Vehicle Model (Parent)
```php
namespace App\Models;

class Vehicle extends Model
{
    public function bookings()
    {
        return $this->morphMany(Booking::class, 'bookable');
    }
}
```

### Facility Model (Parent)
```php
namespace App\Models;

class Facility extends Model
{
    public function bookings()
    {
        return $this->morphMany(Booking::class, 'bookable');
    }
}
```

### Booking Model (Child)
```php
namespace App\Models;

class Booking extends Model
{
    protected $fillable = [
        'user_id', 'category_id', 'bookable_type', 'bookable_id',
        'driver', 'purpose', 'organizer', 'event_name',
        'responsible_person', 'responsible_phone',
        'date_from', 'date_to', 'time_from', 'time_to',
        'status',
    ];

    public function user()
    {
        return $this->belongsTo(User::class);
    }

    public function category()
    {
        return $this->belongsTo(Category::class);
    }

    // Polymorphic inverse: returns Vehicle OR Facility depending on bookable_type
    public function bookable()
    {
        return $this->morphTo();
    }
}
```

## API Usage

### Create Booking (Vehicle)
```bash
POST /api/bookings
{
  "category_id": 2,
  "bookable_type": "App\\Models\\Vehicle",
  "bookable_id": 1,
  "driver": "Pak Budi",
  "purpose": "Kunjungan Lapangan",
  "responsible_person": "Guru Sandi",
  "responsible_phone": "0898765432",
  "date_from": "2026-10-01",
  "date_to": "2026-10-01",
  "time_from": "08:00",
  "time_to": "12:00"
}
```

### Create Booking (Facility)
```bash
POST /api/bookings
{
  "category_id": 6,
  "bookable_type": "App\\Models\\Facility",
  "bookable_id": 1,
  "organizer": "Gereja Bunda Theresa",
  "event_name": "Misa Awal Tahun",
  "responsible_person": "Ibu Maria",
  "responsible_phone": "0812998877",
  "date_from": "2026-10-05",
  "date_to": "2026-10-05",
  "time_from": "07:30",
  "time_to": "10:30"
}
```

### Get Booking with Polymorphic Relationship
```bash
GET /api/bookings/1

Response:
{
  "id": 1,
  "bookable_type": "App\\Models\\Vehicle",
  "bookable_id": 1,
  "bookable": {
    "id": 1,
    "name": "Mobil HIACE",
    "plate_number": "B 1234 PL"
  },
  "user": { ... },
  "category": { ... }
}
```

## Seeding Polymorphic Data

```php
use App\Models\Booking, Category, User, Vehicle;

$user = User::first();
$category = Category::first();

Booking::create([
    'user_id' => $user->id,
    'category_id' => $category->id,
    'bookable_type' => 'App\\Models\\Vehicle',  // Full namespace with escaped backslash
    'bookable_id' => 1,  // ID of Vehicle
    'driver' => 'Pak Budi',
    'purpose' => 'Kunjungan',
    'responsible_person' => 'Guru Sandi',
    'responsible_phone' => '0898765432',
    'date_from' => '2026-10-01',
    'date_to' => '2026-10-01',
    'time_from' => '08:00',
    'time_to' => '12:00',
]);
```

## Key Points
- **polymorphic_type**: Stored as fully-qualified namespace (e.g., `App\Models\Vehicle`). In JSON: `"App\\Models\\Vehicle"` (escaped).
- **polymorphic_id**: Foreign key into the target table (vehicles.id or facilities.id).
- **morphMany()** on Vehicle/Facility: Returns all Bookings of that type.
- **morphTo()** on Booking: Returns either Vehicle OR Facility instance, determined at runtime by `bookable_type`.
- **Query eager loading**: `$bookings->load('bookable')` to avoid N+1 queries.

## Advantages
1. Single unified booking table (no booking_vehicles / booking_facilities tables)
2. Flexible future expansion (can add more resource types without schema changes)
3. Clean API (same endpoint for both vehicle & facility bookings)
4. Shared logic (status approval, date validation, auth checks)
