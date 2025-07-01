import { Tooltip } from "react-tooltip"

type Props = {
    feedback: any
}

const container = `mb-8`
const title = `font-bold mb-4 text-[20px]`
const table = `flex gap-2`
const percentRange = `flex flex-col h-[200px] items-end justify-between
[&_p]:text-[12px]`
const graphContainer = `grow`
const graph = `border-a-orange border-b border-l flex h-[200px] items-end justify-between relative`
const graphBackgroundLine = `absolute bg-a-gray h-[1px] left-0 w-full -z-10`
const graphBarContainer = `flex h-full items-end justify-center px-2`
const graphBar = `bg-a-orange rounded-t-md w-[20px]`
const skillAreas = `flex justify-between`
const skill = `px-2 text-[12px] text-center`

export default function PerformanceBySkill(props: Props){
    return (
        <section className={container}>
            <Tooltip id="tooltip" style={{backgroundColor: 'var(--color-a-darkOrange)'}}/>

            <h2 className={title}>Performance by skill</h2>

            <div className={table}>
                <div className={percentRange}>
                    <p>100%</p>
                    <p>75%</p>
                    <p>50%</p>
                    <p>25%</p>
                    <p>0%</p>
                </div>

                <div className={graphContainer}>
                    <div className={graph}>
                        <div className={graphBackgroundLine} style={{top: '0%'}}></div>
                        <div className={graphBackgroundLine} style={{top: '25%'}}></div>
                        <div className={graphBackgroundLine} style={{top: '50%'}}></div>
                        <div className={graphBackgroundLine} style={{top: '75%'}}></div>
                        
                        {props.feedback.feedbackReport.performanceBySkill.map((performance: any) => {
                            const barHeight = performance.average_score_percent > 5 ? performance.average_score_percent : 5

                            return (
                                <div className={graphBarContainer} key={'percent_' + performance.skill_area} style={{
                                    width: `${(1 / props.feedback.feedbackReport.performanceBySkill.length) * 100}%`
                                }}>
                                    <div className={graphBar} style={{height: `${barHeight}%`}}
                                        data-tooltip-content={`${performance.average_score_percent}%`}
                                        data-tooltip-id="tooltip"
                                    ></div>
                                </div>
                            )
                        })}
                    </div>

                    <div className={skillAreas}>
                        {props.feedback.feedbackReport.performanceBySkill.map((performance: any) =>
                            <p className={skill} key={'skill_' + performance.skill_area} style={{
                                width: `${(1 / props.feedback.feedbackReport.performanceBySkill.length) * 100}%`
                            }}>
                                {performance.skill_area}
                            </p>
                        )}
                    </div>
                </div>
            </div>
        </section>
    )
}