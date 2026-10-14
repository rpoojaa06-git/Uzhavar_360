import type { Service } from '../data/services';
import ServiceTile from './ServiceTile';

export default function ServiceGrid({ services }: { services: Service[] }) {
  return (
    <div className="grid grid-cols-3 gap-2">
      {services.map((s) => (
        <ServiceTile key={s.id} service={s} />
      ))}
    </div>
  );
}
