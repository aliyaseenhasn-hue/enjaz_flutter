import React, { useState, useEffect } from 'react';
import { servicesApi, type Agent } from '../api/services';

interface NearbyAgentsProps {
  userLat?: number;
  userLon?: number;
  radius?: number;
  professionFilter?: string;
}

const NearbyAgents: React.FC<NearbyAgentsProps> = ({
  userLat,
  userLon,
  radius = 10,
  professionFilter
}) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [currentLocation, setCurrentLocation] = useState<{ lat: number; lon: number } | null>(null);

  useEffect(() => {
    findNearbyAgents();
  }, [userLat, userLon, radius, professionFilter]);

  const findNearbyAgents = async () => {
    let lat = userLat;
    let lon = userLon;

    // If user coordinates are not provided, try to get from browser
    if (!lat || !lon) {
      if (navigator.geolocation) {
        setLoading(true);
        navigator.geolocation.getCurrentPosition(
          (position) => {
            setCurrentLocation({
              lat: position.coords.latitude,
              lon: position.coords.longitude
            });
            
            fetchAgents(position.coords.latitude, position.coords.longitude);
          },
          (_err) => {
            setError('فشل الحصول على موقعك. يرجى التأكد من السماح بالوصول للموقع.');
            setLoading(false);
          }
        );
      } else {
        setError('متصفحك لا يدعم خاصية تحديد الموقع الجغرافي.');
        setLoading(false);
      }
    } else {
      // Use provided coordinates
      fetchAgents(lat, lon);
    }
  };

  const fetchAgents = async (lat: number, lon: number) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await servicesApi.getNearbyAgents(lat, lon, radius, professionFilter);
      setAgents(response.agents);
    } catch (err) {
      console.error('Error fetching nearby agents:', err);
      setError('فشل تحميل قائمة المهنيين القريبين. يرجى المحاولة لاحقاً.');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    if (currentLocation) {
      fetchAgents(currentLocation.lat, currentLocation.lon);
    } else if (userLat && userLon) {
      fetchAgents(userLat, userLon);
    } else {
      findNearbyAgents();
    }
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="inline-block animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500 mb-4"></div>
        <p className="text-gray-600">جاري البحث عن المهنيين القريبين...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
        <p>{error}</p>
        <button 
          onClick={handleRefresh}
          className="mt-2 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          إعادة المحاولة
        </button>
      </div>
    );
  }

  return (
    <div className="nearby-agents">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">المهنيون القريبون</h2>
        <button 
          onClick={handleRefresh}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          تحديث
        </button>
      </div>

      {agents.length === 0 ? (
        <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
          <p>لم يتم العثور على مهنيين قريبين في نطاق {radius} كم.</p>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-gray-600">
            تم العثور على {agents.length} مهني{agents.length > 1 ? 'ين' : ''} في نطاق {radius} كم
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((agent) => (
              <div 
                key={agent.id} 
                className="border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="flex items-center mb-3">
                  {agent.avatar ? (
                    <img 
                      src={agent.avatar} 
                      alt={agent.full_name} 
                      className="w-12 h-12 rounded-full object-cover"
                    />
                  ) : (
                    <div className="bg-gray-200 border-2 border-dashed rounded-full w-12 h-12 flex items-center justify-center">
                      <span className="text-gray-500 text-xs">صورة</span>
                    </div>
                  )}
                  
                  <div className="mr-3">
                    <h3 className="font-bold">{agent.full_name}</h3>
                    <p className="text-sm text-gray-600">{agent.profession_display}</p>
                    {agent.is_verified && (
                      <span className="inline-block bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                        موثق
                      </span>
                    )}
                  </div>
                </div>
                
                <div className="mb-2">
                  <p className="text-sm">
                    <span className="font-semibold">المدينة:</span> {agent.city}
                  </p>
                  <p className="text-sm">
                    <span className="font-semibold">المسافة:</span> {agent.distance_km.toFixed(2)} كم
                  </p>
                  <p className="text-sm">
                    <span className="font-semibold">التقييم:</span> {agent.rating} ({agent.total_jobs} عمل)
                  </p>
                  
                  {agent.service_min_price !== null && agent.service_max_price !== null && (
                    <p className="text-sm">
                      <span className="font-semibold">السعر:</span> {agent.service_min_price} - {agent.service_max_price} دينار
                    </p>
                  )}
                </div>
                
                <div className="mt-3">
                  <p className="text-sm text-gray-700 line-clamp-2">{agent.bio}</p>
                </div>
                
                <div className="mt-3 flex space-x-2">
                  <a 
                    href={`tel:${agent.phone_number}`}
                    className="flex-1 bg-blue-500 hover:bg-blue-700 text-white text-center py-2 px-4 rounded"
                  >
                    اتصل
                  </a>
                  <a 
                    href={`sms:${agent.phone_number}`}
                    className="flex-1 bg-green-500 hover:bg-green-700 text-white text-center py-2 px-4 rounded"
                  >
                    رسالة
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default NearbyAgents;