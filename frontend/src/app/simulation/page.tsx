import PageTitle from "@/src/components/global/PageTitle";
import SimulationSelector from "@/src/components/simulation/SimulationSelector";

export default function page(){
    return (
        <>
        <PageTitle text="Conduct Simulation"/>

        <SimulationSelector/>
        </>
    )
}